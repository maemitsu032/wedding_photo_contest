import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import {
  Container, AppBar, Toolbar,
  Typography, Button, Box, createTheme, ThemeProvider, CssBaseline
} from '@mui/material';
import { jaJP } from '@mui/material/locale';

import ImageUpload from './components/ImageUpload';
import Ranking from './components/Ranking';
import AdminRanking from './components/AdminRanking';

// 1. エレガントなカスタムテーマを作成
const theme = createTheme({
  palette: {
    primary: {
      main: '#B388FF', // 淡いパープル
    },
    secondary: {
      main: '#FFC107', // ゴールド
    },
    background: {
      default: '#FDF7E4', // オフホワイト
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Noto Sans JP", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
      color: '#4A148C', // ダークパープル
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#9575CD', // 少し濃いパープル
        },
      },
    },
  },
}, jaJP);


function App() {
  return (
    // 2. ThemeProviderでアプリケーションをラップ
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* CSSのベースラインをリセット・統一 */}
      <div>
        {/* -------- ナビバー -------- */}
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              ウェディング・フォトコンテスト
            </Typography>

            {/* ユーザー向けメニュー */}
            <Button color="inherit" component={Link} to="/">写真投稿</Button>
            <Button color="inherit" component={Link} to="/ranking">ランキング</Button>

            {/* 管理ページへのリンクは非表示 */}
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
              <Route path="/" element={<ImageUpload />} />
              <Route path="/ranking" element={<Ranking />} />
              <Route path="/admin" element={<AdminRanking />} />
            </Routes>
          </Box>
        </Container>
      </div>
    </ThemeProvider>
  );
}

export default App;
