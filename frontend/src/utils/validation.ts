export type ValidationResult = {
  valid: boolean;
  message?: string;
};

const PHONE_PATTERN = /^(?:0|\+84)(?:\d[\s.-]?){8,10}\d$/;
const BANK_ACCOUNT_PATTERN = /^\d{6,20}$/;
const E_WALLET_PATTERN = /^(?:0|\+84)(?:\d[\s.-]?){8,10}\d$/;
const SOCIAL_ACCOUNT_PATTERN = /^[a-zA-Z0-9._@-]{3,64}$/;

export function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export function validateEmailOrPhone(rawValue: string, fieldName = "Email hoặc số điện thoại"): ValidationResult {
  const value = rawValue.trim();
  if (!value) return { valid: false, message: `${fieldName} không được để trống.` };
  if (isValidEmail(value)) return { valid: true };
  if (PHONE_PATTERN.test(value)) return { valid: true };
  return { valid: false, message: `${fieldName} cần là email hợp lệ hoặc số điện thoại bắt đầu bằng 0 hoặc +84.` };
}

export function validateLookupValue(type: string, rawValue: string): ValidationResult {
  const value = rawValue.trim();
  if (!value) {
    return { valid: false, message: "Vui lòng nhập giá trị cần tra cứu." };
  }

  if (type === "phone" && !PHONE_PATTERN.test(value)) {
    return { valid: false, message: "Số điện thoại chỉ được chứa số, có thể bắt đầu bằng 0 hoặc +84. Không nhập ký tự lạ." };
  }

  if (type === "bank_account" && !BANK_ACCOUNT_PATTERN.test(value)) {
    return { valid: false, message: "Tài khoản ngân hàng chỉ được chứa 6-20 chữ số." };
  }

  if (type === "e_wallet" && !E_WALLET_PATTERN.test(value)) {
    return { valid: false, message: "Ví điện tử cần là số điện thoại hợp lệ, không chứa ký tự lạ." };
  }

  if (type === "social_account" && !SOCIAL_ACCOUNT_PATTERN.test(value)) {
    return { valid: false, message: "Tài khoản xã hội chỉ dùng chữ, số, dấu chấm, gạch dưới, gạch ngang hoặc @." };
  }

  return { valid: true };
}

export function validatePhone(rawValue: string, fieldName = "Số điện thoại"): ValidationResult {
  const value = rawValue.trim();
  if (!value) return { valid: false, message: `${fieldName} không được để trống.` };
  if (!PHONE_PATTERN.test(value)) {
    return { valid: false, message: `${fieldName} chỉ được chứa số, có thể bắt đầu bằng 0 hoặc +84. Không nhập ký tự lạ.` };
  }
  return { valid: true };
}

export function validateRequiredText(rawValue: string, fieldName: string, minLength = 1): ValidationResult {
  const value = rawValue.trim();
  if (!value) return { valid: false, message: `${fieldName} không được để trống.` };
  if (value.length < minLength) return { valid: false, message: `${fieldName} cần tối thiểu ${minLength} ký tự.` };
  return { valid: true };
}

export function validateNonNegativeNumber(rawValue: string, fieldName: string): ValidationResult {
  const value = rawValue.trim();
  if (!value) return { valid: true };
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue) || numberValue < 0) {
    return { valid: false, message: `${fieldName} phải là số không âm.` };
  }
  return { valid: true };
}
