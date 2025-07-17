return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>License Admin Panel</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background-color: #121212;
      color: #e0e0e0;
    }
    .form-control, .btn {
      background-color: #1f1f1f;
      color: #fff;
      border: 1px solid #333;
    }
    .form-control:focus, .btn:hover {
      background-color: #2c2c2c;
      border-color: #555;
    }
    .container {
      max-width: 600px;
      margin-top: 40px;
    }
    .card {
      background-color: #1a1a1a;
      border: 1px solid #333;
    }
    hr {
      border-color: #333;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2 class="text-center mb-4">🔐 License Admin Panel</h2>
    <div class="card p-4 mb-4">
      <h4>Add / Update Key</h4>
      <form method="post">
        <div class="mb-3">
          <label class="form-label">License Key</label>
          <input type="text" name="key" class="form-control" required>
        </div>
        <div class="mb-3">
          <label class="form-label">HWID</label>
          <input type="text" name="hwid" class="form-control" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Expiration (ISO optional)</label>
          <input type="text" name="expires" class="form-control">
        </div>
        <button type="submit" class="btn btn-primary w-100">💾 Save Key</button>
      </form>
    </div>

    <div class="card p-4 mb-4">
      <h4>🗑 Delete Key</h4>
      <form action="/admin/delete?pw={{pw}}" method="post">
        <div class="mb-3">
          <label class="form-label">Key to Delete</label>
          <input type="text" name="key" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-danger w-100">Delete Key</button>
      </form>
    </div>

    <div class="text-center">
      <a href="/admin/list?pw={{pw}}" class="btn btn-outline-light">📋 View All Keys</a>
    </div>
  </div>
</body>
</html>
""", pw=pw)
