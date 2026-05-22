import type { ReactNode } from 'react';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <main className="desktop">
      <section className="finder-window">
        <div className="traffic-lights" aria-hidden="true">
          <span className="red" />
          <span className="yellow" />
          <span className="green" />
        </div>
        {children}
      </section>
    </main>
  );
}
