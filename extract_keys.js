const https = require('https');

https.get('https://scholar-flex-seven.vercel.app/assets/index-I_V_Ems8.js', (res) => {
    let data = '';
    res.on('data', d => data += d);
    res.on('end', () => {
        const regex = /localStorage\.getItem\(['"`](.*?)['"`]\)/g;
        let match;
        const keys = new Set();
        while ((match = regex.exec(data)) !== null) {
            keys.add(match[1]);
        }
        
        const setRegex = /localStorage\.setItem\(['"`](.*?)['"`]/g;
        while ((match = setRegex.exec(data)) !== null) {
            keys.add(match[1]);
        }
        
        console.log("Found keys:", Array.from(keys));
    });
});
