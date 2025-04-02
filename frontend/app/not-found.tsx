import Link from "next/link";

export default function NotFound() {
  return (
    <main className="empty-page">
      <section className="empty-state">
        <h1>Page not found</h1>
        <p>The dashboard route you requested does not exist.</p>
        <Link className="primary-link" href="/">
          Return to dashboard
        </Link>
      </section>
    </main>
  );
}
