# OpenTelemetry Weaver Security Policy
# Ensures sensitive attributes are properly marked

package weaver.security

import future.keywords.contains
import future.keywords.if
import future.keywords.in

# Deny sensitive attributes without proper security marking
deny[msg] {
    input.groups[_].attributes[attr]
    is_sensitive_attribute(attr.id)
    not attr.note
    msg := sprintf("Sensitive attribute '%s' must have a security note", [attr.id])
}

# Deny PII attributes at required level
deny[msg] {
    input.groups[_].attributes[attr]
    is_pii_attribute(attr.id)
    attr.requirement_level == "required"
    msg := sprintf("PII attribute '%s' should not be required", [attr.id])
}

# Ensure password attributes are never logged
deny[msg] {
    input.groups[_].attributes[attr]
    contains(lower(attr.id), "password")
    not attr.note
    msg := sprintf("Password attribute '%s' must have security note", [attr.id])
}

# Check for proper sanitization notes
warn[msg] {
    input.groups[_].attributes[attr]
    is_user_input_attribute(attr.id)
    not contains(lower(attr.note), "sanitize")
    not contains(lower(attr.note), "escape")
    msg := sprintf("User input attribute '%s' should mention sanitization", [attr.id])
}

# Helper functions
is_sensitive_attribute(name) {
    sensitive_patterns := [
        "password", "token", "secret", "key", "credential",
        "auth", "private", "confidential"
    ]
    some pattern in sensitive_patterns
    contains(lower(name), pattern)
}

is_pii_attribute(name) {
    pii_patterns := [
        "email", "phone", "ssn", "address", "name",
        "birthday", "ip_address", "location"
    ]
    some pattern in pii_patterns
    contains(lower(name), pattern)
}

is_user_input_attribute(name) {
    input_patterns := [
        "query", "search", "input", "user_data", "message",
        "comment", "description"
    ]
    some pattern in input_patterns
    contains(lower(name), pattern)
}