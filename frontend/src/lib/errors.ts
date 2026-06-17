import { isAxiosError } from "axios";

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item?.msg === "string") {
            return item.msg;
          }
          return JSON.stringify(item);
        })
        .join("; ");
    }
    if (detail) {
      return JSON.stringify(detail);
    }
    if (error.message) {
      return error.message;
    }
  }

  return fallback;
}
