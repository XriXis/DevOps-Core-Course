output "vm_public_ip" {
  description = "Public IP address of the VM."
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "ssh_command" {
  description = "SSH command to connect to VM."
  value       = "ssh -i ~/.ssh/lab04_yc ${var.ssh_user}@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}
