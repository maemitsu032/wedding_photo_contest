import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import ImageUpload from './components/ImageUpload';
import Ranking from './components/Ranking';

function App() {
  return (
    <div>
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            結婚式フォトコンテスト
          </Typography>
          <Button color="inherit" component={Link} to="/">写真投稿</Button>
          <Button color="inherit" component={Link} to="/ranking">ランキング</Button>
        </Toolbar>
      </AppBar>
      
      <Container className="app-container">
        <Box sx={{ my: 4 }}>
          <Routes>
            <Route path="/" element={<ImageUpload />} />
            <Route path="/ranking" element={<Ranking />} />
          </Routes>
        </Box>
      </Container>
    </div>
  );
}

export default App; 