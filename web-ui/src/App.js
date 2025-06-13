import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import {
  Container, AppBar, Toolbar,
  Typography, Button, Box
} from '@mui/material';

import ImageUpload   from './components/ImageUpload';
import Ranking       from './components/Ranking';

/* ⭐️ 追加 ― 管理者一覧ページ */
import AdminRanking  from './components/AdminRanking';   // 置いた場所に合わせてパス調整

function App() {
  return (
    <div>
      {/* -------- ナビバー -------- */}
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            結婚式フォトコンテスト
          </Typography>

          {/* ユーザー向けメニュー */}
          <Button color="inherit" component={Link} to="/">写真投稿</Button>
          <Button color="inherit" component={Link} to="/ranking">ランキング</Button>

          {/* 管理ページへのリンクは  “非表示”  → コメントアウトや環境変数で制御してもよい */}
          {false && (
            <Button color="inherit" component={Link} to="/admin">
              管理
            </Button>
          )}
        </Toolbar>
      </AppBar>

      {/* -------- ルーティング -------- */}
      <Container>
        <Box sx={{ my: 4 }}>
          <Routes>
            <Route path="/"         element={<ImageUpload />} />
            <Route path="/ranking"  element={<Ranking />} />

            {/* ⭐️ 管理者用ページ。URL を直接入力すれば表示できる */}
            <Route path="/admin"    element={<AdminRanking />} />
          </Routes>
        </Box>
      </Container>
    </div>
  );
}

export default App;