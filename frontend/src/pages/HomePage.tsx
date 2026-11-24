import { useQuery } from "@tanstack/react-query";

import { fetchHealth } from "../api/health";

export function HomePage() {
  const health = useQuery({ queryKey: ["health"], queryFn: fetchHealth });

  let apiStatus = "checking…";
  if (health.isSuccess) {
    apiStatus = health.data.status;
  } else if (health.isError) {
    apiStatus = "unreachable";
  }

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="text-3xl font-bold text-gray-900">Vocab App</h1>
      <p className="mt-2 text-gray-600">
        Learn words from your own Excel files.
      </p>
      <p className="mt-4 text-sm text-gray-500">API: {apiStatus}</p>
    </main>
  );
}
