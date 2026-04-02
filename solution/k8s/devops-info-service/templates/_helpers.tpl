{{- define "devops-info-service.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "devops-info-service.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.chart" -}}
{{- include "common.chart" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{ include "common.labels" . }}
{{- $extraLabels := include "common.extraLabels" . -}}
{{- if $extraLabels }}
{{ $extraLabels }}
{{- end }}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{ include "common.selectorLabels" . }}
{{- end -}}

{{- define "devops-info-service.serviceName" -}}
{{- include "devops-info-service.fullname" . -}}
{{- end -}}
