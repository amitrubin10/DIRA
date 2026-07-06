// Cloudflare Worker — live-sync proxy for the DIRA dashboard.
// It fetches the project's inventory feed server-side and returns it WITH CORS
// headers, so the dashboard (amitrubin10.github.io/DIRA) can read it in real time.
// Deploy: dash.cloudflare.com -> Workers & Pages -> Create Worker -> paste -> Deploy.
// Then paste the Worker URL into the dashboard via its ⚙️ button.
export default {
  async fetch(request) {
    const upstream = "https://gl-re.co.il/lp/carmei_gat/data.php";
    const r = await fetch(upstream, {
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://gl-re.co.il/lp/carmei_gat/",
        "Accept": "application/json"
      },
      cf: { cacheTtl: 0 }
    });
    const body = await r.text();
    return new Response(body, {
      status: r.status,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "access-control-allow-origin": "*",
        "cache-control": "no-store"
      }
    });
  }
};
