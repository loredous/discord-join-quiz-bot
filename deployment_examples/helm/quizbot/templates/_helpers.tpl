{{- define "quizbot.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "quizbot.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "quizbot.labels" -}}
app.kubernetes.io/name: {{ include "quizbot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{- define "quizbot.secretName" -}}
{{- if .Values.existingSecret -}}
{{ .Values.existingSecret }}
{{- else -}}
{{ include "quizbot.fullname" . }}-token
{{- end -}}
{{- end -}}

{{- define "quizbot.pvcName" -}}
{{- if .Values.persistence.existingClaim -}}
{{ .Values.persistence.existingClaim }}
{{- else -}}
{{ include "quizbot.fullname" . }}-state
{{- end -}}
{{- end -}}
