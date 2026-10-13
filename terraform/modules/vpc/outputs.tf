output "network_id" {
  description = "VPC Network ID"
  value       = google_compute_network.vpc_network.id
}

output "network_name" {
  description = "VPC Network Name"
  value       = google_compute_network.vpc_network.name
}

output "subnet_id" {
  description = "Primary Subnet ID"
  value       = google_compute_subnetwork.subnet.id
}

output "connector_id" {
  description = "Serverless VPC Access Connector ID"
  value       = google_vpc_access_connector.connector.id
}

output "connector_name" {
  description = "Serverless VPC Access Connector Name"
  value       = google_vpc_access_connector.connector.name
}

output "psa_connection" {
  description = "Private Service Access peering connection"
  value       = google_service_networking_connection.private_vpc_connection
}
