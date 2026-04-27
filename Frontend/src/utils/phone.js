/** Strip non-digits; leading zeros are kept. */
export function normalizePhoneDigits(value) {
  return String(value ?? "").replace(/\D/g, "");
}

/** Exactly ten digit characters (0–9). */
export function isValidPhone10Digits(value) {
  return /^\d{10}$/.test(normalizePhoneDigits(value));
}
