import http from 'http';
import url from 'url';
import path from 'path';
import fs from 'fs';

const PORT = 3000;
const projectRoot = process.cwd();
const uploadDir = path.join(projectRoot, 'uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);

const sendJson = (res, status, data) => {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
};

const server = http.createServer(async (req, res) => {
  const { pathname } = url.parse(req.url, true);

  // Static serve uploads
  if (pathname?.startsWith('/uploads/')) {
    const filePath = path.join(uploadDir, pathname.replace('/uploads/', ''));
    if (fs.existsSync(filePath)) {
      const ext = path.extname(filePath).toLowerCase();
      const type = ext === '.png' ? 'image/png' : 'image/jpeg';
      res.writeHead(200, { 'Content-Type': type });
      fs.createReadStream(filePath).pipe(res);
    } else {
      res.writeHead(404);
      res.end();
    }
    return;
  }

  // Mock Authentication
  if (req.method === 'POST' && pathname === '/users/login') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      // Always succeed
      return sendJson(res, 200, {
        code: 200,
        message: 'Login success',
        data: { token: 'mock-token-123456' }
      });
    });
    return;
  }
  if (req.method === 'POST' && pathname === '/users/register') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      return sendJson(res, 200, {
        code: 200,
        message: 'Register success'
      });
    });
    return;
  }

  // Upload
  if (req.method === 'POST' && (pathname === '/api/upload' || pathname === '/uploads')) {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const json = JSON.parse(body || '{}');
        const { filename = `image_${Date.now()}.png`, contentType = 'image/png', data } = json;
        if (!data) return sendJson(res, 400, { message: 'No data provided' });
        const ext = contentType === 'image/jpeg' ? '.jpg' : '.png';
        const safeBase = path.basename(filename, path.extname(filename));
        const outName = `${safeBase}_${Date.now()}${ext}`;
        const fileBuffer = Buffer.from(data, 'base64');
        fs.writeFileSync(path.join(uploadDir, outName), fileBuffer);


        let cat = 'short_sleeve';
        const lower = filename.toLowerCase();
        if (lower.includes('hoodie') || lower.includes('sweatshirt') || lower.includes('卫衣')) {
          cat = 'hoodie';
        } else if (lower.includes('coat') || lower.includes('jacket') || lower.includes('down') || lower.includes('棉服')) {
          cat = 'coat';
        } else if (lower.includes('jeans') || lower.includes('pants') || lower.includes('trousers') || lower.includes('裤') || lower.includes('bottom')) {
          cat = 'pants';
        } else if (lower.includes('long') || lower.includes('长袖')) {
          cat = 'long_sleeve';
        } else if (lower.includes('short') || lower.includes('tee') || lower.includes('t-shirt') || lower.includes('短袖')) {
          cat = 'short_sleeve';
        }

        return sendJson(res, 200, {
          id: outName,
          name: filename,
          imageUrl: `/uploads/${outName}`,
          uploadDate: new Date().toISOString(),
          category: cat,
          color: json.color || '未知',
        });
      } catch (e) {
        return sendJson(res, 500, { message: 'Upload error', error: String(e) });
      }
    });
    return;
  }

  // Closet Items
  if (req.method === 'GET' && (pathname === '/api/closet' || pathname === '/closet/items')) {
    const files = fs.readdirSync(uploadDir).filter(f => /\.(png|jpg|jpeg)$/i.test(f));
    const items = files.map(f => {
      let cat = 'short_sleeve';
      const lower = f.toLowerCase();
      if (lower.includes('hoodie') || lower.includes('sweatshirt') || lower.includes('卫衣')) {
        cat = 'hoodie';
      } else if (lower.includes('coat') || lower.includes('jacket') || lower.includes('down') || lower.includes('棉服')) {
        cat = 'coat';
      } else if (lower.includes('jeans') || lower.includes('pants') || lower.includes('trousers') || lower.includes('裤') || lower.includes('bottom')) {
        cat = 'pants';
      } else if (lower.includes('long') || lower.includes('长袖')) {
        cat = 'long_sleeve';
      } else if (lower.includes('short') || lower.includes('tee') || lower.includes('t-shirt') || lower.includes('短袖')) {
        cat = 'short_sleeve';
      }
      return {
        id: f,
        name: path.basename(f),
        category: cat,
        color: '未知',
        imageUrl: `/uploads/${f}`,
        uploadDate: new Date(fs.statSync(path.join(uploadDir, f)).mtimeMs).toISOString(),
      };
    });
    // Return format expected by ClosetManager (data.list or just data if array)
    // ClosetManager checks payload.data.list
    return sendJson(res, 200, {
      code: 200,
      message: 'success',
      data: {
        total: items.length,
        list: items
      }
    });
  }

  // Recommendations
  if (req.method === 'GET' && (pathname === '/api/recommendations' || pathname === '/recommend')) {
    const files = fs.readdirSync(uploadDir).filter(f => /\.(png|jpg|jpeg)$/i.test(f));
    const mkItem = (name) => {
      let cat = 'short_sleeve';
      const lower = name.toLowerCase();
      if (lower.includes('hoodie') || lower.includes('sweatshirt') || lower.includes('卫衣')) {
        cat = 'hoodie';
      } else if (lower.includes('coat') || lower.includes('jacket') || lower.includes('down') || lower.includes('棉服')) {
        cat = 'coat';
      } else if (lower.includes('jeans') || lower.includes('pants') || lower.includes('trousers') || lower.includes('裤') || lower.includes('bottom')) {
        cat = 'pants';
      } else if (lower.includes('long') || lower.includes('长袖')) {
        cat = 'long_sleeve';
      } else if (lower.includes('short') || lower.includes('tee') || lower.includes('t-shirt') || lower.includes('短袖')) {
        cat = 'short_sleeve';
      }
      return { id: name, name, category: cat, imageUrl: `/uploads/${name}` };
    };
    // Randomly pick up to 3
    const shuffled = files.sort(() => 0.5 - Math.random());
    const pick = shuffled.slice(0, 3).map(mkItem);

    // Recommendations format
    // RecommendationList checks payload.data (array) or payload.data.list
    const recommendations = [
      {
        title: 'AI 推荐套装',
        weather: '晴天 25°C',
        reason: '根据当前天气，这套搭配清新舒适。',
        outfit: pick,
      }
    ];
    return sendJson(res, 200, {
      code: 200,
      data: recommendations
    });
  }

  res.writeHead(404);
  res.end();
});

server.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
