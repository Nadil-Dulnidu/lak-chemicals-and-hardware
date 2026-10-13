package com.lakchemicals.business.security;

import com.auth0.jwk.Jwk;
import com.auth0.jwk.JwkProvider;
import com.auth0.jwk.JwkProviderBuilder;
import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.interfaces.JWTVerifier;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.URL;
import java.security.interfaces.RSAPublicKey;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

@Slf4j
@Component
public class ClerkJwtVerifier {

    @Value("${clerk.jwks-url:https://delicate-civet-49.clerk.accounts.dev/.well-known/jwks.json}")
    private String jwksUrl;

    @Value("${clerk.issuer:https://delicate-civet-49.clerk.accounts.dev}")
    private String issuer;

    private JwkProvider jwkProvider;
    private final Map<String, JWTVerifier> verifierCache = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        try {
            URL url = URI.create(jwksUrl).toURL();
            this.jwkProvider = new JwkProviderBuilder(url)
                    .cached(10, 24, TimeUnit.HOURS)
                    .rateLimited(10, 1, TimeUnit.MINUTES)
                    .build();
            log.info("Initialized JWK Provider for Clerk with URL: {}", jwksUrl);
        } catch (Exception e) {
            log.error("Failed to initialize Clerk JWK Provider: {}", e.getMessage(), e);
        }
    }

    public DecodedJWT verifyToken(String token) {
        try {
            DecodedJWT decoded = JWT.decode(token);
            String keyId = decoded.getKeyId();

            JWTVerifier verifier = verifierCache.computeIfAbsent(keyId, kid -> {
                try {
                    Jwk jwk = jwkProvider.get(kid);
                    RSAPublicKey publicKey = (RSAPublicKey) jwk.getPublicKey();
                    Algorithm algorithm = Algorithm.RSA256(publicKey, null);
                    return JWT.require(algorithm)
                            .withIssuer(issuer)
                            .build();
                } catch (Exception e) {
                    log.error("Error creating verifier for kid {}: {}", kid, e.getMessage());
                    throw new RuntimeException("Invalid key ID: " + kid, e);
                }
            });

            return verifier.verify(token);
        } catch (Exception e) {
            log.warn("Clerk token verification failed: {}", e.getMessage());
            return null;
        }
    }

    public String extractRole(DecodedJWT jwt) {
        if (jwt == null) return null;

        // Check top-level "role" claim
        var roleClaim = jwt.getClaim("role");
        if (!roleClaim.isNull() && !roleClaim.asString().isEmpty()) {
            return roleClaim.asString();
        }

        // Check nested "public_metadata.role" claim
        var publicMetadataClaim = jwt.getClaim("public_metadata");
        if (!publicMetadataClaim.isNull()) {
            Map<String, Object> map = publicMetadataClaim.asMap();
            if (map != null && map.get("role") != null) {
                return map.get("role").toString();
            }
        }

        return null;
    }
}
