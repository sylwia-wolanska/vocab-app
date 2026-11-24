import { useMutation } from "@tanstack/react-query";
import { Link, Navigate, useLocation } from "react-router";

import { login } from "../api/auth";
import { useAuth } from "../auth/AuthContext";
import { TextField } from "../components/TextField";

type Credentials = { email: string; password: string };

export function LoginPage() {
  const { token, logIn } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const mutation = useMutation({
    mutationFn: ({ email, password }: Credentials) => login(email, password),
    onSuccess: logIn,
  });

  if (token !== null) {
    return <Navigate to={from} replace />;
  }

  return (
    <main className="mx-auto max-w-sm p-6">
      <h1 className="text-2xl font-bold text-gray-900">Log in</h1>
      <form
        className="mt-6 space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          mutation.mutate({
            email: String(form.get("email")),
            password: String(form.get("password")),
          });
        }}
      >
        <TextField
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          required
        />
        <TextField
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
        {mutation.isError && (
          <p role="alert" className="text-sm text-red-600">
            {mutation.error.message}
          </p>
        )}
        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {mutation.isPending ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="mt-4 text-sm text-gray-600">
        No account yet?{" "}
        <Link to="/register" className="text-blue-600 underline">
          Register
        </Link>
      </p>
    </main>
  );
}
