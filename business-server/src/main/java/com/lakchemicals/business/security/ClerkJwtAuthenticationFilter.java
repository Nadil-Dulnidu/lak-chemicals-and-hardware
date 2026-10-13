package com.lakchemicals.business.security;

import com.auth0.jwt.interfaces.DecodedJWT;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class ClerkJwtAuthenticationFilter extends OncePerRequestFilter {

    private final ClerkJwtVerifier clerkJwtVerifier;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String authHeader = request.getHeader("Authorization");

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7).trim();
            DecodedJWT jwt = clerkJwtVerifier.verifyToken(token);

            if (jwt != null) {
                String userId = jwt.getSubject();
                String role = clerkJwtVerifier.extractRole(jwt);

                List<SimpleGrantedAuthority> authorities = new ArrayList<>();
                authorities.add(new SimpleGrantedAuthority("ROLE_USER"));

                if ("ADMIN".equalsIgnoreCase(role)) {
                    authorities.add(new SimpleGrantedAuthority("ROLE_ADMIN"));
                } else {
                    authorities.add(new SimpleGrantedAuthority("ROLE_CUSTOMER"));
                }

                Map<String, Object> details = new HashMap<>();
                details.put("userId", userId);
                details.put("role", role);
                details.put("jwt", jwt);

                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(userId, token, authorities);
                authentication.setDetails(details);

                SecurityContextHolder.getContext().setAuthentication(authentication);
                log.debug("Authenticated Clerk user: {}, role: {}", userId, role);
            } else {
                log.warn("Invalid or expired Clerk JWT provided");
            }
        }

        filterChain.doFilter(request, response);
    }
}
