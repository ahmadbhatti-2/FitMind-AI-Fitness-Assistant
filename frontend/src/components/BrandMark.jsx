export default function BrandMark({ size = 21 }) {
  return (
    <svg
      aria-hidden="true"
      className="brand-symbol"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
    >
      <path d="M7 11v10M11 8v16M21 8v16M25 11v10M11 16h10" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M14 16h4" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round" />
    </svg>
  );
}
