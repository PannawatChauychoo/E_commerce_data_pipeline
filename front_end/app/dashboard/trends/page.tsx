// app/(dashboard)/trends/page.tsx
'use client';

// --- ① ask the token endpoint (or skip if using a public iframe)
const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function PowerBIDashboard() {
  return (
    //@ts-expect-error
    <iframe title="final_ecommerce_9/7" width="1140" height="541.25" src="https://app.powerbi.com/reportEmbed?reportId=4db43bc6-0bb7-4a9b-a717-8eb17089ad51&autoAuth=true&ctid=9ddaaca1-389f-4cb1-a113-081be6cc25fc" frameborder="0" allowFullScreen="true"></iframe>
  );

}
