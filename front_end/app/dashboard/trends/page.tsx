// app/(dashboard)/trends/page.tsx
'use client';

// --- ① ask the token endpoint (or skip if using a public iframe)
const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function PowerBIDashboard() {
  return (
    //@ts-expect-error
    <iframe title="final_ecommerce" width="1140" height="541.25" src="https://app.powerbi.com/reportEmbed?reportId=21f7c4fb-54a5-4b16-a73d-77f863402f09&autoAuth=true&ctid=9ddaaca1-389f-4cb1-a113-081be6cc25fc" allowFullScreen="true"></iframe>
  );

}
