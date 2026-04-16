# Pulumi (Yandex Cloud) for Lab 04

## Files
- `__main__.py`: infrastructure code (VM + VPC + SG)
- `Pulumi.yaml`: project metadata
- `Pulumi.dev.yaml.example`: config template
- `requirements.txt`: dependencies

## Prepare config
1. Create and activate virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `Pulumi.dev.yaml.example` to `Pulumi.dev.yaml`.
4. Replace placeholders with real values.

## Commands
```powershell
cd solution/pulumi
pulumi login
pulumi stack init dev
pulumi preview
pulumi up
pulumi stack output vmPublicIp
pulumi stack output sshCommand
pulumi destroy
```
