/* Japan 2026 offline cache */
const V='j26-v26';const CORE=['./','./index.html','./img/tokyo-hotel.webp','./img/kyoto-apt-1.webp','./img/kyoto-apt-2.webp'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET')return;
  if(u.origin===location.origin&&(u.pathname.endsWith('/')||u.pathname.endsWith('index.html'))){
    // network first for the page, fall back to cache offline
    e.respondWith(fetch(e.request).then(r=>{const c=r.clone();caches.open(V).then(x=>x.put(e.request,c));return r;}).catch(()=>caches.match(e.request).then(r=>r||caches.match('./index.html'))));return;
  }
  if(u.hostname==='images.unsplash.com'||u.pathname.startsWith('/img/')||u.pathname.includes('/img/')||u.hostname.includes('fonts.g')){
    // cache first for images and fonts
    e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(res=>{if(res.ok||res.type==='opaque'){const c=res.clone();caches.open(V).then(x=>x.put(e.request,c));}return res;})));return;
  }
});
