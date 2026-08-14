# quizbot Helm chart

Deploys the Discord Join Quiz Bot with its quiz configuration rendered into
a ConfigMap and a PersistentVolumeClaim for the bot's state file (attempt
counts, etc.), so an in-progress quiz cadence survives pod restarts.

## Usage

```sh
helm install quizbot ./deployment_examples/helm/quizbot \
  --set botToken=your-discord-bot-token \
  -f my-quiz-values.yaml
```

Where `my-quiz-values.yaml` overrides `quizConfig` with your server's real
guild/channel/role IDs and questions (see `example_quiz.yaml` in the repo
root for the full schema).

To source the token from an existing Secret instead of `--set botToken=...`,
set `existingSecret` (and optionally `existingSecretKey`, default
`bot-token`).

This chart only supports a single replica: quiz progress is tracked
in-process and persisted to one PVC, so running more than one pod would
race on state and duplicate quizzes.
