{{- define "devops-info-service-rust.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "devops-info-service-rust.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "devops-info-service-rust.labels" -}}
{{ include "common.labels" . }}
{{- $extraLabels := include "common.extraLabels" . -}}
{{- if $extraLabels }}
{{ $extraLabels }}
{{- end }}
{{- end -}}

{{- define "devops-info-service-rust.selectorLabels" -}}
{{ include "common.selectorLabels" . }}
{{- end -}}
