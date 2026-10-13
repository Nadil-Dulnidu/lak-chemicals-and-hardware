resource "google_compute_network" "vpc_network" {
  name                    = "${lower(var.project_name)}-${lower(var.environment)}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${lower(var.project_name)}-${lower(var.environment)}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc_network.id
  project       = var.project_id

  private_ip_google_access = true
}

# Private Service Access for Cloud SQL & Redis
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "${lower(var.project_name)}-${lower(var.environment)}-psa-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# Serverless VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "${lower(var.environment)}-vpc-conn"
  region        = var.region
  project       = var.project_id
  ip_cidr_range = var.connector_cidr
  network       = google_compute_network.vpc_network.name

  min_instances = var.connector_min_instances
  max_instances = var.connector_max_instances
  machine_type  = "e2-micro"

  depends_on = [google_compute_network.vpc_network]
}

# Cloud Router & NAT for Outbound Internet
resource "google_compute_router" "router" {
  name    = "${lower(var.project_name)}-${lower(var.environment)}-router"
  region  = var.region
  network = google_compute_network.vpc_network.id
  project = var.project_id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${lower(var.project_name)}-${lower(var.environment)}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
