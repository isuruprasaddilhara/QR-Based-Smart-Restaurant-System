export const ROLE_ACCESS = {
  admin: {
    pages: [
      "dashboard",
      "menu",
      "tables",
      "settings",
      "users",
      "reports",
    ],
  },
  cashier: {
    pages: ["dashboard", "menu", "tables", "settings"],
  },
  kitchen: {
    pages: ["orders", "settings"],
  },
  customer: {
    pages: [],
  },
};

export function canAccess(role, page) {
  return ROLE_ACCESS[role]?.pages?.includes(page) ?? false;
}
