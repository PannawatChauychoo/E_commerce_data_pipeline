// app/(dashboard)/trends/page.tsx
'use client';

// --- ① ask the token endpoint (or skip if using a public iframe)
const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function PowerBIDashboard() {
  return (
  <iframe title="final_ecommerce" className='min-h-[680px] w-full border-2-black' src="https://app.powerbi.com/view?r=eyJrIjoiN2ZmZjFiODMtZjUzZS00N2I4LTliMzUtMjU2ZTRmMTVjOGIzIiwidCI6IjlkZGFhY2ExLTM4OWYtNGNiMS1hMTEzLTA4MWJlNmNjMjVmYyIsImMiOjZ9" allowFullScreen={true}>
  </iframe>
);

}
