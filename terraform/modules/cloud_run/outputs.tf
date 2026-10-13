output "business_server_uri" {
  description = "Spring Boot Business Server Cloud Run URI"
  value       = google_cloud_run_v2_service.business_server.uri
}

output "ai_service_uri" {
  description = "FastAPI Multi-Agent AI Service Cloud Run URI"
  value       = google_cloud_run_v2_service.ai_service.uri
}


output "web_uri" {
  description = "Next.js Web Client Cloud Run URI"
  value       = google_cloud_run_v2_service.web.uri
}
