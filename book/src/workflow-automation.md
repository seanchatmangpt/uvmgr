# Workflow Automation

uvmgr supports workflow automation using BPMN and scheduling tools.

## Run BPMN Workflows

```bash
uvmgr agent run my-workflow.bpmn
```

## Schedule Recurring Tasks

```bash
uvmgr ap-scheduler add --cron "0 0 * * *" --task "uvmgr tests run"
```

Automate complex workflows and recurring jobs with ease. 