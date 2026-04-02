{{/*
Return the chart name or an override.
*/}}
{{- define "common.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Return a full resource name that stays under the Kubernetes DNS label limit.
*/}}
{{- define "common.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := include "common.name" . -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Return the chart version label.
*/}}
{{- define "common.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Selector labels shared by all application charts.
*/}}
{{- define "common.selectorLabels" -}}
app.kubernetes.io/name: {{ include "common.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Standard Kubernetes application labels.
*/}}
{{- define "common.labels" -}}
helm.sh/chart: {{ include "common.chart" . }}
{{ include "common.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: {{ default "web" .Values.component | quote }}
app.kubernetes.io/part-of: {{ default .Chart.Name .Values.partOf | quote }}
{{- end -}}

{{/*
Render arbitrary user labels if present.
*/}}
{{- define "common.extraLabels" -}}
{{- if .Values.extraLabels -}}
{{- toYaml .Values.extraLabels -}}
{{- end -}}
{{- end -}}

{{/*
Render environment variables from a list of name/value pairs.
*/}}
{{- define "common.envList" -}}
{{- range . }}
- name: {{ .name | quote }}
  value: {{ .value | quote }}
{{- end -}}
{{- end -}}

{{/*
Render an HTTP probe block from values.
*/}}
{{- define "common.httpProbe" -}}
httpGet:
  path: {{ .path | quote }}
  port: {{ .port }}
initialDelaySeconds: {{ .initialDelaySeconds }}
periodSeconds: {{ .periodSeconds }}
timeoutSeconds: {{ .timeoutSeconds }}
failureThreshold: {{ .failureThreshold }}
{{- if hasKey . "successThreshold" }}
successThreshold: {{ .successThreshold }}
{{- end }}
{{- end -}}
