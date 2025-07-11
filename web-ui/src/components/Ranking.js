import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Grid, Card, CardContent, CardMedia,
  CircularProgress, Alert, Tabs, Tab, Chip, Avatar
} from '@mui/material';
import { collection, getDocs } from 'firebase/firestore';
import { ref, getDownloadURL } from 'firebase/storage';
import { db, storage } from '../firebase';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'; // ?アイコン
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents'; // ランキングアイコン

const COLLECTION = 'contestScores';

export default function Ranking() {
  const [entries, setEntries] = useState([]);
  const [targetTypes, setTargetTypes] = useState([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /* ------------- Firestore 取得 ------------- */
  useEffect(() => {
    (async () => {
      try {
        const snap = await getDocs(collection(db, COLLECTION));
        const promises = [];
        const targetsSet = new Set();

        snap.forEach(doc => {
          const data = doc.data();
          const scores = data.scores || {};
          Object.keys(scores).forEach(k => targetsSet.add(k));

          promises.push(
            getDownloadURL(ref(storage, data.path))
              .catch(() => '')
              .then(url => ({
                id: doc.id,
                userName: data.userName ?? '(名無し)',
                imgUrl: url,
                faceCnt: data.faceCount ?? 0,
                scores
              }))
          );
        });

        const docs = await Promise.all(promises);
        // ユーザー名でソートしておく
        docs.sort((a, b) => a.userName.localeCompare(b.userName, 'ja'));

        setTargetTypes(Array.from(targetsSet));
        setEntries(docs);
      } catch (e) {
        console.error(e);
        setError('ランキングデータの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  /* ------------- 表示用データ生成 ------------- */
  const sortedEntries = () => {
    const key = targetTypes[selected] ?? '';

    // スコア降順 → 同名ユーザーは最初の1件のみ採用
    const base = [...entries].sort(
      (a, b) => (b.scores[key] ?? -Infinity) - (a.scores[key] ?? -Infinity)
    );

    const seen = new Set();
    const uniqueEntries = base.filter(e => {
      if (seen.has(e.userName)) return false;
      seen.add(e.userName);
      return true;
    });

    // 上位5名を名前順でシャッフル、6位以下はスコア順のまま
    const top5 = uniqueEntries.slice(0, 5).sort((a, b) =>
      a.userName.localeCompare(b.userName, 'ja')
    );
    const others = uniqueEntries.slice(5);

    return [...top5, ...others];
  };

  /* ------------- UIコンポーネント ------------- */
  if (loading) return <Center><CircularProgress /></Center>;
  if (error) return <Center><Alert severity="error">{error}</Alert></Center>;

  return (
    <Paper sx={{ p: 3, backgroundColor: 'transparent', boxShadow: 'none' }}>
      <Typography variant="h4" align="center" gutterBottom sx={{ mb: 3 }}>
        フォトコンテスト ランキング
      </Typography>

      {targetTypes.length > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
          <Tabs
            value={selected}
            onChange={(_, v) => setSelected(v)}
            variant="scrollable"
            scrollButtons="auto"
          >
            {targetTypes.map(t => <Tab key={t} label={t} />)}
          </Tabs>
        </Box>
      )}

      {entries.length === 0 ? (
        <Center><Typography>まだ投稿がありません</Typography></Center>
      ) : (
        <Grid container spacing={4}>
          {sortedEntries().map((entry, idx) => (
            <Grid item key={entry.id} xs={12} sm={6} md={4}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardMedia
                  component="img"
                  height="200"
                  image={entry.imgUrl || 'https://via.placeholder.com/300'}
                  alt={`Photo by ${entry.userName}`}
                  sx={{ objectFit: 'cover' }}
                />
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" component="div" noWrap>
                    {entry.userName}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, mb: 1 }}>
                    {idx < 5 ? (
                      <Chip
                        icon={<HelpOutlineIcon />}
                        label="トップ5候補！"
                        color="secondary"
                        variant="filled"
                      />
                    ) : (
                      <Chip
                        icon={<EmojiEventsIcon />}
                        label={`${idx + 1}位`}
                        color="primary"
                        variant="outlined"
                      />
                    )}
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    スコア: {idx < 5 ? '???' : `${(entry.scores[targetTypes[selected]] * 100).toFixed(1)} 点`}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Paper>
  );
}

function Center({ children }) {
  return <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>{children}</Box>;
}

