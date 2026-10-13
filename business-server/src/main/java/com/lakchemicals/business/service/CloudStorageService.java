package com.lakchemicals.business.service;

import com.google.cloud.storage.BlobId;
import com.google.cloud.storage.BlobInfo;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageOptions;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.UUID;

@Slf4j
@Service
public class CloudStorageService {

    @Value("${gcp.storage.bucket-name:lak-chemicals-products}")
    private String bucketName;

    @Value("${gcp.storage.public-url-prefix:https://storage.googleapis.com/lak-chemicals-products}")
    private String publicUrlPrefix;

    private Storage storage;

    public CloudStorageService() {
        try {
            this.storage = StorageOptions.getDefaultInstance().getService();
        } catch (Exception e) {
            log.warn("Could not initialize Google Cloud Storage with default credentials: {}", e.getMessage());
            this.storage = null;
        }
    }

    public String uploadImage(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            return null;
        }

        String originalFilename = file.getOriginalFilename();
        String extension = "";
        if (originalFilename != null && originalFilename.contains(".")) {
            extension = originalFilename.substring(originalFilename.lastIndexOf("."));
        }

        String blobName = "products/" + UUID.randomUUID() + extension;

        if (storage != null) {
            try {
                BlobId blobId = BlobId.of(bucketName, blobName);
                BlobInfo blobInfo = BlobInfo.newBuilder(blobId)
                        .setContentType(file.getContentType())
                        .build();

                storage.create(blobInfo, file.getBytes());
                String publicUrl = publicUrlPrefix + "/" + blobName;
                log.info("Uploaded product image to GCS: {}", publicUrl);
                return publicUrl;
            } catch (Exception e) {
                log.error("Failed to upload image to GCS: {}", e.getMessage(), e);
                // Fallback to placeholder/mock URL in dev
                return "https://storage.googleapis.com/" + bucketName + "/" + blobName;
            }
        } else {
            log.info("GCS Storage client not available, returning simulated image URL for {}", blobName);
            return "https://storage.googleapis.com/" + bucketName + "/" + blobName;
        }
    }

    public boolean deleteImage(String imageUrl) {
        if (imageUrl == null || storage == null) {
            return false;
        }

        try {
            String prefix = publicUrlPrefix + "/";
            if (imageUrl.startsWith(prefix)) {
                String blobName = imageUrl.substring(prefix.length());
                BlobId blobId = BlobId.of(bucketName, blobName);
                return storage.delete(blobId);
            }
        } catch (Exception e) {
            log.error("Failed to delete image from GCS: {}", e.getMessage());
        }
        return false;
    }
}
