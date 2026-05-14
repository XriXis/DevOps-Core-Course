variable "sa_key_file" {
  description = "Path to Yandex Cloud authorized key JSON file."
  type        = string
}

variable "cloud_id" {
  description = "Yandex Cloud ID."
  type        = string
}

variable "folder_id" {
  description = "Yandex Folder ID where resources will be created."
  type        = string
}

variable "zone" {
  description = "Yandex Cloud availability zone."
  type        = string
  default     = "ru-central1-d"
}

variable "project_name" {
  description = "Prefix for resource names."
  type        = string
  default     = "lab04"
}

variable "subnet_cidr" {
  description = "CIDR block for subnet."
  type        = string
  default     = "10.10.0.0/24"
}

variable "image_family" {
  description = "Image family for VM boot disk."
  type        = string
  default     = "ubuntu-2404-lts"
}

variable "ssh_user" {
  description = "Linux user for SSH access."
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to local public SSH key."
  type        = string
}

variable "my_ip_cidr" {
  description = "Your public IP in CIDR, example: 1.2.3.4/32."
  type        = string
}
