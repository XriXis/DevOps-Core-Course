# Terraform (Yandex Cloud) for Lab 04

## 1. Prepare variables
1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Fill these values:
   - `sa_key_file`
   - `cloud_id`
   - `folder_id`
   - `ssh_public_key_path`
   - `my_ip_cidr`

## 2. Run Terraform
```powershell
cd solution/terraform
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## 3. Connect to VM
Use output values:
```powershell
terraform output vm_public_ip
terraform output ssh_command
```

Or connect directly:
```powershell
ssh -i $env:USERPROFILE\.ssh\lab04_yc ubuntu@<VM_PUBLIC_IP>
```

## 4. Cleanup
```powershell
terraform destroy
```
