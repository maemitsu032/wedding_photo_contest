import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, List, ListItem,
  ListItemText, ListItemAvatar, Avatar, Divider,
  CircularProgress, Alert, Tabs, Tab, Tooltip
} from '@mui/material';
import { collection, getDocs } from 'firebase/firestore';
import { ref, getDownloadURL } from 'firebase/storage';
import { db, storage } from '../firebase';
import PhotoIcon from '@mui/icons-material/Photo';
import InfoIcon from '@mui/icons-material/Info';

const COLLECTION = 'contestScores';

export default function Ranking() {
  const [entries, setEntries]         = useState([]);
  const [targetTypes, setTargetTypes] = useState([]);
  const [selected, setSelected]       = useState(0);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);

  /* ------------- Firestore 取得 ------------- */
  useEffect(() => {
    (async () => {
      try {
        const snap = await getDocs(collection(db, COLLECTION));
        const promises   = [];
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

  /* ------------- util ------------- */
  const inflate = s => (s * 100).toFixed(1);

  const sortedEntries = () => {
    const key = targetTypes[selected] ?? '';

    // スコア降順 → 同名 1 件 → Top5 を名前順
    const base = [...entries].sort(
      (a, b) => (b.scores[key] ?? -Infinity) - (a.scores[key] ?? -Infinity)
    );

    const seen = new Set();
    const uniq = base.filter(e => {
      if (seen.has(e.userName)) return false;
      seen.add(e.userName);
      return true;
    });

    const top5   = uniq.slice(0, 5).sort((a, b) =>
      a.userName.localeCompare(b.userName, 'ja')
    );
    const others = uniq.slice(5);

    return [...top5, ...others];
  };

  const rankLabel = idx => (idx < 5 ? 'Top5' : `${idx + 1}.`);

  /* ------------- UI ------------- */
  if (loading) return <Center><CircularProgress /></Center>;
  if (error)   return <Center><Alert severity="error">{error}</Alert></Center>;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h4" align="center" gutterBottom>
        フォトコンテスト ランキング
      </Typography>

      {targetTypes.length > 0 && (
        <Tabs
          value={selected}
          onChange={(_, v) => setSelected(v)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ mb: 2 }}
        >
          {targetTypes.map(t => <Tab key={t} label={t} />)}
        </Tabs>
      )}

      {entries.length === 0 ? (
        <Center>まだ投稿がありません</Center>
      ) : (
        <List>
          {sortedEntries().map((e, idx) => (
            <React.Fragment key={e.id}>
              {idx > 0 && <Divider component="li" />}
              <ListItem>
                <ListItemAvatar>
                  <Avatar src={e.imgUrl}><PhotoIcon /></Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={`${rankLabel(idx)} ${e.userName}`}
                  secondary={
                    <>
                      スコア: {idx < 5
                        ? '???'
                        : inflate(e.scores[targetTypes[selected]] || 0)} 点
                      <Tooltip title="スコアは顔類似度を元に算出">
                        <InfoIcon
                          fontSize="small"
                          sx={{ ml: 1, verticalAlign: 'middle' }}
                        />
                      </Tooltip>
                      {` — 顔検出: ${e.faceCnt} 人`}
                    </>
                  }
                />
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}
    </Paper>
  );
}

function Center({ children }) {
  return <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>{children}</Box>;
}
