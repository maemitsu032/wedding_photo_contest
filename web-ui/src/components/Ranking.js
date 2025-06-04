import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemAvatar, 
  Avatar,
  Divider,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Tooltip
} from '@mui/material';
import { collection, query, orderBy, limit, onSnapshot } from 'firebase/firestore';
import { db } from '../firebase';
import PhotoIcon from '@mui/icons-material/Photo';
import InfoIcon from '@mui/icons-material/Info';

const Ranking = () => {
  const [topEntries, setTopEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [targetTypes, setTargetTypes] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState(0);

  useEffect(() => {
    // Firestoreからデータを取得するクエリ
    const photosRef = collection(db, 'photos');
    
    // スコアの高い順にクエリを作成（同一ユーザーの場合は最高スコアを使用）
    const q = query(
      photosRef,
      orderBy('score', 'desc'),
      limit(50) // 多めに取得して後で処理
    );

    // リアルタイムリスナーを設定
    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        // ユーザーごとの最高スコアを記録
        const userHighestScores = {};
        const allTargetTypes = new Set();
        
        snapshot.docs.forEach(doc => {
          const data = doc.data();
          const userName = data.userName;
          const score = data.score || 0;
          
          // ターゲットタイプを検出（score_で始まるフィールド）
          Object.keys(data).forEach(key => {
            if (key.startsWith('score_') && key !== 'score') {
              allTargetTypes.add(key.replace('score_', ''));
            }
          });
          
          // ユーザーの最高スコアを記録
          if (!userHighestScores[userName] || score > userHighestScores[userName].score) {
            userHighestScores[userName] = {
              id: doc.id,
              userName,
              score,
              photoUrl: data.photoUrl,
              faceCount: data.faceCount || 0,
              timestamp: data.timestamp,
              // 各ターゲットスコアを追加
              targetScores: Object.entries(data)
                .filter(([key]) => key.startsWith('score_'))
                .reduce((obj, [key, value]) => {
                  obj[key.replace('score_', '')] = value;
                  return obj;
                }, {})
            };
          }
        });
        
        // 配列に変換
        const entries = Object.values(userHighestScores);
        
        // 名前順にソート（要件：順位順ではなく文字列順）
        entries.sort((a, b) => a.userName.localeCompare(b.userName, 'ja'));
        
        // トップ10を取得
        const top10 = entries.slice(0, 10);
        
        // 利用可能なターゲットタイプを設定
        const targetTypesArray = Array.from(allTargetTypes);
        setTargetTypes(['総合'].concat(targetTypesArray));
        
        setTopEntries(top10);
        setLoading(false);
      },
      (err) => {
        console.error('ランキングデータの取得エラー:', err);
        setError('ランキングデータの取得に失敗しました。');
        setLoading(false);
      }
    );

    // クリーンアップ関数
    return () => unsubscribe();
  }, []);

  // タブ変更ハンドラ
  const handleTabChange = (event, newValue) => {
    setSelectedTarget(newValue);
  };

  // 選択されたターゲットに基づいてソートされたエントリを取得
  const getSortedEntries = () => {
    if (selectedTarget === 0) {
      // 総合スコアでソート
      return [...topEntries].sort((a, b) => a.userName.localeCompare(b.userName, 'ja'));
    } else {
      // 特定のターゲットスコアでソート
      const targetName = targetTypes[selectedTarget];
      return [...topEntries].sort((a, b) => a.userName.localeCompare(b.userName, 'ja'));
    }
  };

  // スコア表示用の関数
  const formatScore = (score) => {
    return (score * 100).toFixed(1);
  };

  // 現在選択されているターゲットのスコアを取得
  const getTargetScore = (entry) => {
    if (selectedTarget === 0) {
      return entry.score;
    } else {
      const targetName = targetTypes[selectedTarget];
      return entry.targetScores?.[targetName] || 0;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 4 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Paper className="ranking-container" elevation={3}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        フォトコンテスト参加者
      </Typography>
      
      <Typography variant="body1" paragraph align="center" color="text.secondary">
        以下は参加者の一覧です（名前順）
      </Typography>
      
      {targetTypes.length > 0 && (
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs 
            value={selectedTarget} 
            onChange={handleTabChange} 
            variant="scrollable"
            scrollButtons="auto"
          >
            {targetTypes.map((targetName, index) => (
              <Tab 
                key={index} 
                label={targetName} 
                id={`target-tab-${index}`}
                aria-controls={`target-tabpanel-${index}`}
              />
            ))}
          </Tabs>
        </Box>
      )}
      
      {topEntries.length === 0 ? (
        <Typography variant="body1" align="center" sx={{ my: 4 }}>
          まだ参加者がいません。写真をアップロードして最初の参加者になりましょう！
        </Typography>
      ) : (
        <List>
          {getSortedEntries().map((entry, index) => (
            <React.Fragment key={entry.id}>
              {index > 0 && <Divider variant="inset" component="li" />}
              <ListItem alignItems="flex-start">
                <ListItemAvatar>
                  <Avatar alt={entry.userName} src={entry.photoUrl}>
                    <PhotoIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Typography variant="subtitle1" component="span">
                      {entry.userName}
                    </Typography>
                  }
                  secondary={
                    <React.Fragment>
                      <Typography variant="body2" component="span" color="text.primary">
                        スコア: {formatScore(getTargetScore(entry))}点
                        <Tooltip title="スコアは顔検出と類似度に基づく値です">
                          <InfoIcon fontSize="small" sx={{ ml: 1, verticalAlign: 'middle', fontSize: '0.9rem' }} />
                        </Tooltip>
                      </Typography>
                      {" — "}
                      <Typography variant="body2" component="span">
                        検出された顔: {entry.faceCount}
                      </Typography>
                      
                      {/* 選択されたターゲットに対するスコアの詳細 */}
                      {selectedTarget !== 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2">
                            {targetTypes[selectedTarget]}に対するスコア: {formatScore(getTargetScore(entry))}点
                          </Typography>
                        </Box>
                      )}
                      
                      {/* すべてのターゲットスコアを表示するオプション（折りたたみ可能） */}
                      {entry.targetScores && Object.keys(entry.targetScores).length > 0 && (
                        <Box 
                          sx={{ 
                            mt: 1, 
                            p: 1, 
                            bgcolor: 'rgba(0,0,0,0.03)', 
                            borderRadius: 1,
                            display: 'none' // 通常は非表示
                          }}
                          className="all-scores"
                        >
                          {Object.entries(entry.targetScores).map(([targetName, score]) => (
                            <Typography key={targetName} variant="body2" sx={{ fontSize: '0.75rem' }}>
                              {targetName}: {formatScore(score)}点
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </React.Fragment>
                  }
                />
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default Ranking; 