import type { ComponentProps } from "react";

type TextFieldProps = ComponentProps<"input"> & { label: string };

export function TextField({ label, ...inputProps }: TextFieldProps) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <input
        {...inputProps}
        className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-blue-500 focus:outline-none"
      />
    </label>
  );
}
