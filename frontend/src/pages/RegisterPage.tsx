import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate } from "react-router";

import { login, register } from "../api/auth";
import { useAuth } from "../auth/AuthContext";
import { TextField } from "../components/TextField";

type Credentials = { email: string; password: string };

export function RegisterPage() {
  const { token, logIn } = useAuth();
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async ({ email, password }: Credentials) => {
      await register(email, password);
      return login(email, password);
    },
    onSuccess: logIn,
  });

  if (token !== null) {
    return <Navigate to="/" replace />;
  }

  const error = formError ?? mutation.error?.message;

  return (
    <main className="mx-auto max-w-sm p-6">
      <h1 className="text-2xl font-bold text-gray-900">Create an account</h1>
      <form
        className="mt-6 space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          const password = String(form.get("password"));
          if (password !== String(form.get("repeatPassword"))) {
            setFormError("The passwords do not match");
            return;
          }
          setFormError(null);
          mutation.mutate({ email: String(form.get("email")), password });
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
          label="Password (at least 8 characters)"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          maxLength={128}
          required
        />
        <TextField
          label="Repeat password"
          name="repeatPassword"
          type="password"
          autoComplete="new-password"
          required
        />
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {mutation.isPending ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className="mt-4 text-sm text-gray-600">
        Already have an account?{" "}
        <Link to="/login" className="text-blue-600 underline">
          Log in
        </Link>
      </p>
    </main>
  );
}
