import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./styles.css";

export const metadata: Metadata = {
  title: "NetHealth",
  description: "ISP network monitoring and assurance",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="app-header">
            <span className="brand-mark" aria-hidden="true">
              N
            </span>
            <div>
              <strong>NetHealth</strong>
              <span className="subtitle">Network assurance platform</span>
            </div>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
