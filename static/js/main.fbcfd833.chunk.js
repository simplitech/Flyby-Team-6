(this["webpackJsonpn3-smart-contract-web-app"]=this["webpackJsonpn3-smart-contract-web-app"]||[]).push([[0],{35:function(e,t,n){},60:function(e,t,n){},66:function(e,t,n){"use strict";n.r(t);var c=n(0),r=n.n(c),a=n(29),i=n.n(a),o=(n(35),n(8)),s=n.n(o),j=n(19),u=n(9),b=n(11),d=n.n(b),f=n(13),l=n(2),h=n.p+"static/media/logo.49aa5273.svg",O=n.p+"static/media/1.bd030e55.jpg",p=(n.p,n.p,n.p,n(60),n(1));function x(){var e=Object(c.useState)(""),t=Object(u.a)(e,2),n=t[0],r=t[1],a=Object(c.useState)(!1),i=Object(u.a)(a,2),o=i[0],f=i[1],l=Object(c.useState)(!1),h=Object(u.a)(l,2),O=h[0],x=h[1],m="https://testnet1.neo.coz.io";function g(e){return v.apply(this,arguments)}function v(){return(v=Object(j.a)(s.a.mark((function e(t){var n;return s.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return n=new d.a.experimental.SmartContract(d.a.u.HexString.fromHex("0xf9ffa64482b38c0dc7841cf27d25a9f03dfb0381"),{networkMagic:t.networkMagic,rpcAddress:t.nodeUrl,account:t.fromAccount}),e.next=3,n.invoke("request_image_change",[]);case 3:case"end":return e.stop()}}),e)})))).apply(this,arguments)}function k(){return(k=Object(j.a)(s.a.mark((function e(){var t,c;return s.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:t=new b.wallet.Account(n),c={fromAccount:t,tokenScriptHash:"0xf9ffa64482b38c0dc7841cf27d25a9f03dfb0381",amountToTransfer:.1,systemFee:0,networkFee:0,networkMagic:844378958,nodeUrl:m},x(!0),g(c).then((function(){x(!1)}));case 4:case"end":return e.stop()}}),e)})))).apply(this,arguments)}return Object(c.useEffect)((function(){b.wallet.isWIF(n)&&f(!0)}),[n]),Object(p.jsx)(p.Fragment,{children:O?Object(p.jsx)("div",{children:Object(p.jsx)("p",{children:"Invoking the smart contract..."})}):o?Object(p.jsx)("button",{onClick:function(){return k.apply(this,arguments)},children:" CLICK TO INVOKE "}):Object(p.jsxs)("form",{children:[Object(p.jsx)("input",{onChange:function(e){return r(e.target.value)},type:"text"}),Object(p.jsx)("input",{type:"submit"})]})})}function m(e){var t=e.invokeDetected;return Object(p.jsx)("div",{id:"frame-container",children:Object(p.jsx)("div",{id:"frame",children:t&&Object(p.jsx)("img",{className:"animate-flicker ",src:O,id:"hero"})})})}var g=function(){var e=Object(c.useState)(0),t=Object(u.a)(e,2),n=t[0],r=t[1],a=Object(c.useState)(!1),i=Object(u.a)(a,2),o=i[0],s=i[1];return Object(c.useEffect)((function(){new WebSocket("wss://dora.coz.io/ws/v1/neo3/testnet/log/0xf9ffa64482b38c0dc7841cf27d25a9f03dfb0381").onmessage=function(e){var t=JSON.parse(e.data);r(t.height),t.log&&t.log.notifications.find((function(e){return"ChangeImage"===e.event_name}))&&(s(!0),setTimeout((function(){s(!1)}),1e4))}})),console.log({invokeDetected:o}),Object(p.jsxs)("div",{className:"App",children:[Object(p.jsx)("img",{id:"neo-logo",src:h}),Object(p.jsx)(f.a,{children:Object(p.jsxs)("div",{children:[Object(p.jsxs)("nav",{children:[Object(p.jsxs)("code",{children:[" ","websocket connection to dora live: current block height:"," ",n]}),Object(p.jsxs)("ul",{children:[Object(p.jsx)("li",{children:Object(p.jsx)(f.b,{to:"/",children:"Party time"})}),Object(p.jsx)("li",{children:Object(p.jsx)(f.b,{to:"/invoke-contract",children:"Invoke Contract"})})]})]}),Object(p.jsxs)(l.c,{children:[Object(p.jsx)(l.a,{path:"/invoke-contract",children:Object(p.jsx)(x,{})}),Object(p.jsx)(l.a,{path:"/",children:Object(p.jsx)(m,{invokeDetected:o})})]})]})})]})},v=function(e){e&&e instanceof Function&&n.e(3).then(n.bind(null,67)).then((function(t){var n=t.getCLS,c=t.getFID,r=t.getFCP,a=t.getLCP,i=t.getTTFB;n(e),c(e),r(e),a(e),i(e)}))};i.a.render(Object(p.jsx)(r.a.StrictMode,{children:Object(p.jsx)(g,{})}),document.getElementById("root")),v()}},[[66,1,2]]]);
//# sourceMappingURL=main.fbcfd833.chunk.js.map