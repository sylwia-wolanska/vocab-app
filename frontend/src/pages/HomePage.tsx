import { useQuery } from "@tanstack/react-query";

import { getMe } from "../api/auth";
import { fetchHealth } from "../api/health";
import { useAuth } from "../auth/AuthContext";

export function HomePage() {
  const { logOut } = useAuth();
  const me = useQuery({ queryKey: ["me"], queryFn: getMe });
  const health = useQuery({ queryKey: ["health"], queryFn: fetchHealth });

  let apiStatus = "checking…";
  if (health.isSuccess) {
    apiStatus = health.data.status;
  } else if (health.isError) {
    apiStatus = "unreachable";
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <header className="flex items-center justify-between gap-4">
        <h1 className="text-3xl font-bold text-gray-900">Vocab App</h1>
        <button
          type="button"
          onClick={logOut}
          className="rounded-lg border border-gray-300 px-3 py-1 text-sm text-gray-700"
        >
          Log out
        </button>
      </header>
      {me.isSuccess && (
        <p className="mt-1 text-sm text-gray-500">
          Logged in as {me.data.email}
        </p>
      )}
      <p className="mt-2 text-gray-600">
        Learn words from your own Excel files.
      </p>
      <p className="mt-4 text-sm text-gray-500">API: {apiStatus}</p>
    </main>
  );
}
