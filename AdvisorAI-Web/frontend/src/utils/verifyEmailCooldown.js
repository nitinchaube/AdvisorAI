// Shared helpers for the "Resend Verification Email" cooldown timer.
// Both the signup auto-send path (AuthContext) and the manual-resend
// path (EmailVerification) write to the same key so the timer persists
// across navigations / refreshes.

export const VERIFY_EMAIL_COOLDOWN_SECONDS = 120; // 2 minutes
export const VERIFY_EMAIL_COOLDOWN_KEY = "verifyEmailCooldownExpiry";

export function startVerifyEmailCooldown(seconds = VERIFY_EMAIL_COOLDOWN_SECONDS) {
  try {
    const expiryTime = Date.now() + seconds * 1000;
    localStorage.setItem(VERIFY_EMAIL_COOLDOWN_KEY, expiryTime.toString());
    return expiryTime;
  } catch {
    // localStorage may be unavailable (private mode, quota, etc.).
    // Failing silently is fine — worst case, the user sees no timer.
    return null;
  }
}

export function getRemainingVerifyEmailCooldown() {
  try {
    const savedExpiry = localStorage.getItem(VERIFY_EMAIL_COOLDOWN_KEY);
    if (!savedExpiry) return 0;
    const remaining = Math.ceil((parseInt(savedExpiry, 10) - Date.now()) / 1000);
    if (remaining > 0) return remaining;
    localStorage.removeItem(VERIFY_EMAIL_COOLDOWN_KEY);
    return 0;
  } catch {
    return 0;
  }
}

export function clearVerifyEmailCooldown() {
  try {
    localStorage.removeItem(VERIFY_EMAIL_COOLDOWN_KEY);
  } catch {
    // ignore
  }
}
