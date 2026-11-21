"""Views for projects, cohort imports and allocation runs."""

import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from allocations.allocator.engine import allocate
from allocations.allocator.result import Status
from allocations.forms import AllocationForm, CohortUploadForm, ProjectForm
from allocations.models import AllocationRun, Project, Student
from allocations.policies.attainment import AttainmentPolicy
from allocations.policies.base import get_violations
from allocations.policies.gender import GenderPolicy
from allocations.policies.team_size import TeamSizePolicy


def _accessible_projects(user):
    projects = Project.objects.all()
    if not user.is_superuser:
        projects = projects.filter(owner=user)
    return projects


def _get_project(user, project_id):
    return get_object_or_404(_accessible_projects(user), id=project_id)


@login_required
def project_list(request):
    """List projects available to the signed-in staff user."""
    projects = _accessible_projects(request.user).prefetch_related('students')
    return render(request, 'project_list.html', {'projects': projects})


@login_required
def project_create(request):
    """Create a project and import its initial cohort."""
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                project = Project.objects.create(
                    owner=request.user,
                    name=form.cleaned_data['name'],
                )
                Student.objects.bulk_create([
                    Student(project=project, **student_data)
                    for student_data in form.cleaned_data['students']
                ])
            messages.success(request, 'Project created and cohort imported.')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    return render(request, 'project_form.html', {'form': form})


@login_required
def project_detail(request, project_id):
    """Show cohort contents and allocation actions for one project."""
    project = _get_project(request.user, project_id)
    students = list(project.students.all())
    return render(request, 'project_detail.html', {
        'project': project,
        'students': students,
        'upload_form': CohortUploadForm(),
        'allocation_form': AllocationForm(students=students),
        'runs': project.allocation_runs.all(),
    })


@login_required
def cohort_upload(request, project_id):
    """Replace a project's cohort only after the uploaded CSV validates."""
    project = _get_project(request.user, project_id)
    if request.method != 'POST':
        return redirect('project_detail', project_id=project.id)

    form = CohortUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'project_detail.html', {
            'project': project,
            'students': list(project.students.all()),
            'upload_form': form,
            'allocation_form': AllocationForm(students=project.students.all()),
            'runs': project.allocation_runs.all(),
        })

    with transaction.atomic():
        project.students.all().delete()
        Student.objects.bulk_create([
            Student(project=project, **student_data)
            for student_data in form.cleaned_data['students']
        ])
    messages.success(request, 'The project cohort has been replaced.')
    return redirect('project_detail', project_id=project.id)


@login_required
def allocation_create(request, project_id):
    """Run the unchanged allocator and save the result and policy checks."""
    project = _get_project(request.user, project_id)
    students = list(project.students.all())
    if request.method != 'POST':
        return redirect('project_detail', project_id=project.id)

    form = AllocationForm(request.POST, students=students)
    if not form.is_valid():
        return render(request, 'project_detail.html', {
            'project': project,
            'students': students,
            'upload_form': CohortUploadForm(),
            'allocation_form': form,
            'runs': project.allocation_runs.all(),
        })

    options = {
        'check_gender': form.cleaned_data['check_gender'],
        'check_attainment': form.cleaned_data['check_attainment'],
        'max_spread': form.cleaned_data['max_spread'],
    }
    policies = [TeamSizePolicy(
        min_size=form.cleaned_data['min_team_size'],
        max_size=form.cleaned_data['max_team_size'],
    )]
    evaluation_policies = []
    if options['check_gender']:
        evaluation_policies.append(GenderPolicy())
    if options['check_attainment']:
        evaluation_policies.append(AttainmentPolicy(max_spread=options['max_spread']))

    result = allocate(students, policies)
    teams = []
    violations = []
    if result.status == Status.SUCCESS:
        teams = [
            {
                'name': team.name,
                'students': [
                    {
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'email': student.email,
                    }
                    for student in team.students
                ],
            }
            for team in result.teams
        ]
        violations = [
            {
                'policy_name': violation.policy_name,
                'team_name': violation.team_name,
                'message': violation.message,
            }
            for violation in get_violations(result.teams, evaluation_policies)
        ]

    allocation_run = AllocationRun.objects.create(
        project=project,
        status=result.status.value,
        message=result.message,
        min_team_size=policies[0].min_size,
        max_team_size=policies[0].max_size,
        policies=options,
        teams=teams,
        violations=violations,
    )
    return redirect('allocation_run_detail', project_id=project.id, run_id=allocation_run.id)


@login_required
def allocation_run_detail(request, project_id, run_id):
    """Inspect one saved allocation and its post-allocation policy findings."""
    project = _get_project(request.user, project_id)
    allocation_run = get_object_or_404(project.allocation_runs, id=run_id)
    return render(request, 'allocation_run_detail.html', {
        'project': project,
        'allocation_run': allocation_run,
    })


@login_required
def allocation_export(request, project_id, run_id):
    """Export a successful allocation in the prescribed four-column format."""
    project = _get_project(request.user, project_id)
    allocation_run = get_object_or_404(project.allocation_runs, id=run_id)
    if allocation_run.status != Status.SUCCESS.value:
        messages.error(request, 'Only successful allocation runs can be exported.')
        return redirect(
            'allocation_run_detail',
            project_id=project.id,
            run_id=allocation_run.id,
        )

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="allocation-{allocation_run.id}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['first_name', 'last_name', 'email', 'team'])
    for team in allocation_run.teams:
        for student in team['students']:
            writer.writerow([
                student['first_name'],
                student['last_name'],
                student['email'],
                team['name'],
            ])
    return response
