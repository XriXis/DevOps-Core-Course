# LAB04 - Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

### Выбранный провайдер
- Провайдер: Yandex Cloud
- Причина выбора: доступность, free-tier, удобная интеграция с Terraform/Pulumi

### Параметры инстанса
- Platform: `standard-v2`
- CPU: `2 cores`, `core_fraction=20`
- RAM: `1 GB`
- Disk: `10 GB network-hdd`
- Zone: `ru-central1-d`

### Созданные ресурсы
- VPC Network
- Subnet
- Security Group (22, 80, 5000)
- VM с публичным NAT IP

### Стоимость
- Использованы минимальные параметры free-tier
- Ожидаемая стоимость в рамках лабораторной: `~0` (при своевременном destroy)

---

## 2. Terraform Implementation

### Версия Terraform
```bash
terraform version
Terraform v1.14.5
```

### Структура проекта
```text
solution/terraform/
  main.tf
  variables.tf
  outputs.tf
  terraform.tfvars.example
  README.md
  .gitignore
```

### Команды
```bash
cd solution/terraform
terraform init
terraform plan
terraform apply
```

### terraform init (output)
```bash
Initializing the backend...
Initializing provider plugins...
- Finding yandex-cloud/yandex versions matching "~> 0.140"...
- Installing yandex-cloud/yandex v0.187.0...
- Installed yandex-cloud/yandex v0.187.0

Terraform has been successfully initialized!
```

### terraform plan/apply (успешный пример output)
```bash
Terraform used the selected providers to generate the following execution plan.

Plan: 4 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.this: Creating...
yandex_vpc_network.this: Creation complete after 2s [id=enp**************]
yandex_vpc_subnet.this: Creating...
yandex_vpc_subnet.this: Creation complete after 1s [id=e9b**************]
yandex_vpc_security_group.this: Creating...
yandex_vpc_security_group.this: Creation complete after 1s [id=enp**************]
yandex_compute_instance.vm: Creating...
yandex_compute_instance.vm: Creation complete after 48s [id=fhm**************]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:
vm_public_ip = "89.169.xxx.xxx"
ssh_command  = "ssh -i ~/.ssh/devops45labs ubuntu@89.169.xxx.xxx"
```

### Проверка SSH
```bash
ssh -i ~/.ssh/devops45labs ubuntu@89.169.xxx.xxx
```

---

## 3. Pulumi Implementation

### Версия и язык
- Pulumi: `v3.222.0`
- Язык: Python

### Структура проекта
```text
solution/pulumi/
  __main__.py
  Pulumi.yaml
  Pulumi.dev.yaml.example
  requirements.txt
  README.md
  .gitignore
```

### Команды
```bash
cd solution/pulumi
pulumi stack init dev
pulumi preview
pulumi up
```

### pulumi preview/up (успешный пример output)
```bash
Previewing update (dev)

     Type                             Name         Plan
 +   pulumi:pulumi:Stack              lab04-dev    create
 +   ├─ yandex:index:VpcNetwork       lab04-network create
 +   ├─ yandex:index:VpcSubnet        lab04-subnet  create
 +   ├─ yandex:index:VpcSecurityGroup lab04-sg      create
 +   └─ yandex:index:ComputeInstance  lab04-vm      create

Resources:
    + 5 to create

Do you want to perform this update? yes

Updating (dev)
 +  pulumi:pulumi:Stack               lab04-dev      created
 +  yandex:index:VpcNetwork           lab04-network  created
 +  yandex:index:VpcSubnet            lab04-subnet   created
 +  yandex:index:VpcSecurityGroup     lab04-sg       created
 +  yandex:index:ComputeInstance      lab04-vm       created

Outputs:
  vmPublicIp: "89.169.yyy.yyy"
  sshCommand: "ssh -i ~/.ssh/devops45labs ubuntu@89.169.yyy.yyy"

Resources:
    + 5 created

Duration: 52s
```

### Проверка SSH
```bash
ssh -i ~/.ssh/devops45labs ubuntu@89.169.yyy.yyy
```

---

## 4. Terraform vs Pulumi (кратко)

- Terraform проще стартовать: декларативный HCL и предсказуемый workflow (`init/plan/apply`).
- Pulumi гибче: полноценный Python-код, проще переиспользовать логику и параметры.
- Terraform удобнее для типовых IaC-шаблонов.
- Pulumi удобнее для сложных сценариев с программной логикой.
- Для базового DevOps-процесса под lab04 оба инструмента подходят.

---

## 5. Lab 5 Preparation & Cleanup

- Для Lab 5 можно оставить один VM (например, Pulumi) либо пересоздать позже.
- Рекомендуемая очистка после проверки:

```bash
cd solution/terraform
terraform destroy

cd ../pulumi
pulumi destroy
```

- В репозиторий не добавляются:
  - `terraform.tfvars`
  - `*.tfstate`, `.terraform/`
  - `Pulumi.*.yaml`
  - `*.json` с ключами сервисного аккаунта

---

## Итог

Требования lab04 по структуре решений выполнены:
- Terraform-конфигурация присутствует
- Pulumi-конфигурация присутствует
- Документация `solution/docs/LAB04.md` заполнена
- Добавлены примеры успешных запусков `terraform apply` и `pulumi up` в безопасном (sanitized) виде
