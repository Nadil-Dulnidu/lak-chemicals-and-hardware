output "bucket_name" {
  description = "Name of the GCS product images bucket"
  value       = google_storage_bucket.product_images.name
}

output "bucket_url" {
  description = "Base URL of the GCS product images bucket"
  value       = google_storage_bucket.product_images.url
}
