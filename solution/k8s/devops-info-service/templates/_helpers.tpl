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

{{- define "devops-info-service.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{- printf "%s-secret" (include "devops-info-service.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else -}}
{{- include "devops-info-service.fullname" . -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.configFileMapName" -}}
{{- if .Values.configMaps.file.name -}}
{{- .Values.configMaps.file.name -}}
{{- else -}}
{{- printf "%s-config" (include "devops-info-service.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.envConfigMapName" -}}
{{- if .Values.configMaps.env.name -}}
{{- .Values.configMaps.env.name -}}
{{- else -}}
{{- printf "%s-env" (include "devops-info-service.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.pvcName" -}}
{{- if .Values.persistence.name -}}
{{- .Values.persistence.name -}}
{{- else -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: DEBUG
  value: {{ .Values.env.debug | quote }}
- name: RELEASE_VERSION
  value: {{ .Values.env.releaseVersion | quote }}
- name: CONFIG_PATH
  value: {{ .Values.env.configPath | quote }}
- name: VISITS_FILE
  value: {{ .Values.env.visitsFile | quote }}
{{- end -}}

{{- define "devops-info-service.vaultAnnotations" -}}
{{- if .Values.vault.enabled }}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/auth-path: {{ .Values.vault.authPath | quote }}
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-inject-secret-{{ .Values.vault.injectFileName }}: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/agent-inject-secret-{{ .Values.vault.templateFileName }}: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/agent-inject-template-{{ .Values.vault.templateFileName }}: |
  {{ "{{- with secret \"" }}{{ .Values.vault.secretPath }}{{ "\" -}}" }}
  APP_USERNAME={{ "{{ .Data.data." }}{{ .Values.vault.secrets.usernameKey }}{{ " }}" }}
  APP_PASSWORD={{ "{{ .Data.data." }}{{ .Values.vault.secrets.passwordKey }}{{ " }}" }}
  {{ "{{- end }}" }}
{{- if .Values.vault.injectCommand }}
vault.hashicorp.com/agent-inject-command-{{ .Values.vault.templateFileName }}: {{ .Values.vault.injectCommand | quote }}
{{- end }}
{{- end }}
{{- end -}}
