PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS cards (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pack            TEXT    NOT NULL CHECK (pack IN ('Black Bolt','Journey Together','Stormfront')),
    name            TEXT    NOT NULL,
    english_no      TEXT    NOT NULL,
    variant_index   INTEGER NOT NULL DEFAULT 1,
    type            TEXT    NOT NULL,
    rarity          TEXT    NOT NULL,
    image_url       TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cards_pack_no_variant
ON cards(pack, english_no, variant_index);

-- ===== Favorites  =====
PRAGMA foreign_keys = ON;

-- One favorite per References cards.
CREATE TABLE IF NOT EXISTS user_favorite_guild (
    guild_id TEXT    NOT NULL,
    user_id  TEXT    NOT NULL,
    card_id  INTEGER NOT NULL,
    set_ts   INTEGER NOT NULL,                -- unix timestamp
    PRIMARY KEY (guild_id, user_id),
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Disallow favoriting a card the user doesn't own in that guild.

CREATE TRIGGER IF NOT EXISTS trg_fav_insert_must_own
BEFORE INSERT ON user_favorite_guild
BEGIN
  SELECT CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM user_collection_guild
       WHERE guild_id = NEW.guild_id
         AND user_id  = NEW.user_id
         AND card_id  = NEW.card_id
    )
    THEN RAISE(ABORT, 'favorite card must be owned by user in this guild')
  END;
END;

CREATE TRIGGER IF NOT EXISTS trg_fav_update_must_own
BEFORE UPDATE OF card_id ON user_favorite_guild
BEGIN
  SELECT CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM user_collection_guild
       WHERE guild_id = NEW.guild_id
         AND user_id  = NEW.user_id
         AND card_id  = NEW.card_id
    )
    THEN RAISE(ABORT, 'favorite card must be owned by user in this guild')
  END;
END;

-- Convenience view to join favorite details for profiles quickly
CREATE VIEW IF NOT EXISTS v_user_favorite_detail AS
SELECT
  f.guild_id,
  f.user_id,
  f.card_id           AS favorite_card_id,
  f.set_ts            AS favorite_set_ts,
  c.name              AS favorite_name,
  c.rarity            AS favorite_rarity,
  c.english_no        AS favorite_no,
  c.image_url         AS favorite_image_url
FROM user_favorite_guild f
JOIN cards c ON c.id = f.card_id;

-- (Optional helper SQL you might call from Python)
-- UPSERT favorite only if owned:
-- INSERT INTO user_favorite_guild (guild_id, user_id, card_id, set_ts)
-- SELECT ?, ?, ?, strftime('%s','now')
-- WHERE EXISTS (
--   SELECT 1 FROM user_collection_guild
--    WHERE guild_id = ? AND user_id = ? AND card_id = ?
-- )
-- ON CONFLICT(guild_id, user_id)
-- DO UPDATE SET card_id=excluded.card_id, set_ts=excluded.set_ts;

-- Fetch favorite (detail):
-- SELECT favorite_card_id, favorite_name, favorite_rarity, favorite_no, favorite_image_url
--   FROM v_user_favorite_detail
--  WHERE guild_id=? AND user_id=?;

-- Clear favorite:
-- DELETE FROM user_favorite_guild WHERE guild_id=? AND user_id=?;

BEGIN;
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Snivy','001/086',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/7/73/SnivyBlackBolt1.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Servine','002/086',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/1/10/ServineBlackBolt2.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Serperior ex','003/086',1,'Grass','Double Rare','https://archives.bulbagarden.net/media/upload/7/77/SerperiorexBlackBolt3.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Pansage','004/086',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/a/a5/PansageBlackBolt4.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Simisage','005/086',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/8/82/SimisageBlackBolt5.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Petilil','006/086',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/c/cd/PetililBlackBolt6.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Lilligant','007/086',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/9/90/LilligantBlackBolt7.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Maractus','008/086',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/d/de/MaractusBlackBolt8.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Karrablast','009/086',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/4/47/KarrablastBlackBolt9.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Foongus','010/086',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/6/6e/FoongusBlackBolt10.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Amoonguss','011/086',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/4/42/AmoongussBlackBolt11.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Victini','012/086',1,'Fire','Rare','https://archives.bulbagarden.net/media/upload/1/1e/VictiniBlackBolt12.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Darumaka','013/086',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/f/f0/DarumakaBlackBolt13.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Darmanitan','014/086',1,'Fire','Uncommon','https://archives.bulbagarden.net/media/upload/5/5b/DarmanitanBlackBolt14.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Larvesta','015/086',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/7/76/LarvestaBlackBolt15.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Volcarona','016/086',1,'Fire','Rare','https://archives.bulbagarden.net/media/upload/7/76/VolcaronaBlackBolt16.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Panpour','017/086',1,'Water','Common','https://archives.bulbagarden.net/media/upload/2/23/PanpourBlackBolt17.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Simipour','018/086',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/6/64/SimipourBlackBolt18.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tympole','019/086',1,'Water','Common','https://archives.bulbagarden.net/media/upload/b/b4/TympoleBlackBolt19.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Palpitoad','020/086',1,'Water','Common','https://archives.bulbagarden.net/media/upload/1/13/PalpitoadBlackBolt20.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Seismitoad','021/086',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/b/b5/SeismitoadBlackBolt21.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tirtouga','022/086',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/d/d2/TirtougaBlackBolt22.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Carracosta','023/086',1,'Water','Rare','https://archives.bulbagarden.net/media/upload/9/9a/CarracostaBlackBolt23.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Alomomola','024/086',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/5/56/AlomomolaBlackBolt24.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cubchoo','025/086',1,'Water','Common','https://archives.bulbagarden.net/media/upload/d/d7/CubchooBlackBolt25.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Beartic','026/086',1,'Water','Rare','https://archives.bulbagarden.net/media/upload/5/5e/BearticBlackBolt26.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cryogonal','027/086',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/f/f0/CryogonalBlackBolt27.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Kyurem ex','028/086',1,'Water','Double Rare','https://archives.bulbagarden.net/media/upload/c/c9/KyuremexBlackBolt28.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Emolga','029/086',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/f/f8/EmolgaBlackBolt29.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tynamo','030/086',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/8/8d/TynamoBlackBolt30.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Eelektrik','031/086',1,'Lightning','Uncommon','https://archives.bulbagarden.net/media/upload/3/3d/EelektrikBlackBolt31.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Eelektross','032/086',1,'Lightning','Uncommon','https://archives.bulbagarden.net/media/upload/2/24/EelektrossBlackBolt32.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Thundurus','033/086',1,'Lightning','Rare','https://archives.bulbagarden.net/media/upload/b/b7/ThundurusBlackBolt33.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Zekrom ex','034/086',1,'Lightning','Double Rare','https://archives.bulbagarden.net/media/upload/2/23/ZekromexBlackBolt34.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Munna','035/086',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/a/a9/MunnaBlackBolt35.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Musharna','036/086',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/0/00/MusharnaBlackBolt36.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Solosis','037/086',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/4/4e/SolosisBlackBolt37.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Duosion','038/086',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/d/df/DuosionBlackBolt38.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Reuniclus','039/086',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/5/53/ReuniclusBlackBolt39.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Elgyem','040/086',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/0/05/ElgyemBlackBolt40.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Beheeyem','041/086',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/2/2a/BeheeyemBlackBolt41.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Golett','042/086',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/3/3e/GolettBlackBolt42.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Golurk','043/086',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/2/24/GolurkBlackBolt43.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Meloetta ex','044/086',1,'Psychic','Double Rare','https://archives.bulbagarden.net/media/upload/6/60/MeloettaexBlackBolt44.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Drilbur','045/086',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/1/1e/DrilburBlackBolt45.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Excadrill ex','046/086',1,'Fighting','Double Rare','https://archives.bulbagarden.net/media/upload/b/be/ExcadrillexBlackBolt46.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Timburr','047/086',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/7/76/TimburrBlackBolt47.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Gurdurr','048/086',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/e/e2/GurdurrBlackBolt48.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Conkeldurr','049/086',1,'Fighting','Rare','https://archives.bulbagarden.net/media/upload/5/57/ConkeldurrBlackBolt49.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Throh','050/086',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/b/b8/ThrohBlackBolt50.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Dwebble','051/086',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/4/4a/DwebbleBlackBolt51.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Crustle','052/086',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/9/9c/CrustleBlackBolt52.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Landorus','053/086',1,'Fighting','Rare','https://archives.bulbagarden.net/media/upload/d/de/LandorusBlackBolt53.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Venipede','054/086',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/9/96/VenipedeBlackBolt54.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Whirlipede','055/086',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/d/dd/WhirlipedeBlackBolt55.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Scolipede','056/086',1,'Darkness','Uncommon','https://archives.bulbagarden.net/media/upload/4/41/ScolipedeBlackBolt56.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Sandile','057/086',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/6/6b/SandileBlackBolt57.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Krokorok','058/086',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/4/4e/KrokorokBlackBolt58.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Krookodile','059/086',1,'Darkness','Uncommon','https://archives.bulbagarden.net/media/upload/0/01/KrookodileBlackBolt59.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Escavalier','060/086',1,'Metal','Uncommon','https://archives.bulbagarden.net/media/upload/0/07/EscavalierBlackBolt60.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Klink','061/086',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/1/1f/KlinkBlackBolt61.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Klang','062/086',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/f/fb/KlangBlackBolt62.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Klinklang','063/086',1,'Metal','Rare','https://archives.bulbagarden.net/media/upload/9/99/KlinklangBlackBolt63.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Pawniard','064/086',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/3/38/PawniardBlackBolt64.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Bisharp','065/086',1,'Metal','Uncommon','https://archives.bulbagarden.net/media/upload/a/a1/BisharpBlackBolt65.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cobalion','066/086',1,'Metal','Rare','https://archives.bulbagarden.net/media/upload/b/b2/CobalionBlackBolt66.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Genesect ex','067/086',1,'Metal','Double Rare','https://archives.bulbagarden.net/media/upload/c/cb/GenesectexBlackBolt67.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Axew','068/086',1,'Dragon','Common','https://archives.bulbagarden.net/media/upload/d/d2/AxewBlackBolt68.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Fraxure','069/086',1,'Dragon','Common','https://archives.bulbagarden.net/media/upload/7/76/FraxureBlackBolt69.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Haxorus','070/086',1,'Dragon','Rare','https://archives.bulbagarden.net/media/upload/3/3c/HaxorusBlackBolt70.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Pidove','071/086',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/0/05/PidoveBlackBolt71.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tranquill','072/086',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/0/06/TranquillBlackBolt72.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Unfezant','073/086',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/1/19/UnfezantBlackBolt73.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Audino','074/086',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/b/b3/AudinoBlackBolt74.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Minccino','075/086',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/d/de/MinccinoBlackBolt75.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cinccino','076/086',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/d/d6/CinccinoBlackBolt76.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Rufflet','077/086',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/3/3e/RuffletBlackBolt77.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Braviary','078/086',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/a/ad/BraviaryBlackBolt78.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Air Balloon','079/086',1,'Trainer','Uncommon','https://archives.bulbagarden.net/media/upload/d/d8/AirBalloonBlackBolt79.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Antique Cover Fossil','080/086',1,'Trainer','Common','https://archives.bulbagarden.net/media/upload/c/cb/AntiqueCoverFossilStellarCrown129.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Energy Coin','081/086',1,'Trainer','Uncommon','https://archives.bulbagarden.net/media/upload/5/5b/EnergyCoinBlackBolt81.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Fennel','082/086',1,'Trainer','Uncommon','https://archives.bulbagarden.net/media/upload/4/47/FennelBlackBolt82.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','N''s Plan','083/086',1,'Trainer','Uncommon','https://archives.bulbagarden.net/media/upload/2/2f/NPlanBlackBolt83.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Pokégear 3.0','084/086',1,'Trainer','Uncommon','https://archives.bulbagarden.net/media/upload/c/cb/Pok%C3%A9gear3.0UnbrokenBonds182b.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Professor''s Research [Professor Juniper]','085/086',1,'Trainer','Uncommon','https://archives.bulbagarden.net/media/upload/a/a2/ProfessorResearchShiningFates60.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Prism Energy','086/086',1,'Energy','Uncommon','https://archives.bulbagarden.net/media/upload/3/3e/PrismEnergyBlackBolt86.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Snivy','087/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/9/90/SnivyBlackBolt87.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Servine','088/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/6/67/ServineBlackBolt88.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Pansage','089/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/fc/PansageBlackBolt89.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Simisage','090/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/0/08/SimisageBlackBolt90.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Petilil','091/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/7/7a/PetililBlackBolt91.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Lilligant','092/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/a/a7/LilligantBlackBolt92.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Maractus','093/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/c/c9/MaractusBlackBolt93.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Karrablast','094/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/6/6a/KarrablastBlackBolt94.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Foongus','095/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/6/6c/FoongusBlackBolt95.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Amoonguss','096/086',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/3/31/AmoongussBlackBolt96.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Darumaka','097/086',1,'Fire','Illustration Rare','https://archives.bulbagarden.net/media/upload/1/16/DarumakaBlackBolt97.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Darmanitan','098/086',1,'Fire','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/f1/DarmanitanBlackBolt98.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Larvesta','099/086',1,'Fire','Illustration Rare','https://archives.bulbagarden.net/media/upload/2/21/LarvestaBlackBolt99.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Volcarona','100/086',1,'Fire','Illustration Rare','https://archives.bulbagarden.net/media/upload/9/94/VolcaronaBlackBolt100.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Panpour','101/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/c/c8/PanpourBlackBolt101.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Simipour','102/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/8/8e/SimipourBlackBolt102.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tympole','103/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/d/d8/TympoleBlackBolt103.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Palpitoad','104/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/8/8d/PalpitoadBlackBolt104.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Seismitoad','105/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/a/a6/SeismitoadBlackBolt105.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tirtouga','106/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/8/8b/TirtougaBlackBolt106.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Carracosta','107/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/a/aa/CarracostaBlackBolt107.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Alomomola','108/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/9/96/AlomomolaBlackBolt108.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cubchoo','109/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/d/d6/CubchooBlackBolt109.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Beartic','110/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/a/a6/BearticBlackBolt110.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cryogonal','111/086',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/2/2d/CryogonalBlackBolt111.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Emolga','112/086',1,'Lightning','Illustration Rare','https://archives.bulbagarden.net/media/upload/3/30/EmolgaBlackBolt112.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tynamo','113/086',1,'Lightning','Illustration Rare','https://archives.bulbagarden.net/media/upload/0/03/TynamoBlackBolt113.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Eelektrik','114/086',1,'Lightning','Illustration Rare','https://archives.bulbagarden.net/media/upload/b/b4/EelektrikBlackBolt114.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Eelektross','115/086',1,'Lightning','Illustration Rare','https://archives.bulbagarden.net/media/upload/9/99/EelektrossBlackBolt115.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Munna','116/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/4/48/MunnaBlackBolt116.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Musharna','117/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/fa/MusharnaBlackBolt117.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Solosis','118/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/7/71/SolosisBlackBolt118.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Duosion','119/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/0/07/DuosionBlackBolt119.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Elgyem','120/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/9/9a/ElgyemBlackBolt120.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Beheeyem','121/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/fe/BeheeyemBlackBolt121.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Golett','122/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/e/e8/GolettBlackBolt122.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Golurk','123/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/b/b4/GolurkBlackBolt123.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Drilbur','124/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/d/df/DrilburBlackBolt124.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Timburr','125/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/e/e3/TimburrBlackBolt125.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Gurdurr','126/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/b/b1/GurdurrBlackBolt126.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Conkeldurr','127/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/e/e6/ConkeldurrBlackBolt127.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Throh','128/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/2/2d/ThrohBlackBolt128.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Dwebble','129/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/7/7c/DwebbleBlackBolt129.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Crustle','130/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/c/c4/CrustleBlackBolt130.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Landorus','131/086',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/3/37/LandorusBlackBolt131.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Venipede','132/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/4/40/VenipedeBlackBolt132.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Whirlipede','133/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/f1/WhirlipedeBlackBolt133.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Scolipede','134/086',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/1/19/ScolipedeBlackBolt134.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Sandile','135/086',1,'Darkness','Illustration Rare','https://archives.bulbagarden.net/media/upload/a/a6/SandileBlackBolt135.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Krokorok','136/086',1,'Darkness','Illustration Rare','https://archives.bulbagarden.net/media/upload/d/d4/KrokorokBlackBolt136.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Krookodile','137/086',1,'Darkness','Illustration Rare','https://archives.bulbagarden.net/media/upload/8/8f/KrookodileBlackBolt137.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Escavalier','138/086',1,'Metal','Illustration Rare','https://archives.bulbagarden.net/media/upload/1/1a/EscavalierBlackBolt138.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Klink','139/086',1,'Metal','Illustration Rare','https://archives.bulbagarden.net/media/upload/d/dd/KlinkBlackBolt139.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Klang','140/086',1,'Metal','Illustration Rare','https://archives.bulbagarden.net/media/upload/1/18/KlangBlackBolt140.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Klinklang','141/086',1,'Metal','Illustration Rare','https://archives.bulbagarden.net/media/upload/1/12/KlinklangBlackBolt141.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Pawniard','142/086',1,'Darkness','Illustration Rare','https://archives.bulbagarden.net/media/upload/3/3a/PawniardBlackBolt142.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Bisharp','143/086',1,'Darkness','Illustration Rare','https://archives.bulbagarden.net/media/upload/7/7b/BisharpBlackBolt143.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cobalion','144/086',1,'Metal','Illustration Rare','https://archives.bulbagarden.net/media/upload/6/6f/CobalionBlackBolt144.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Axew','145/086',1,'Dragon','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/f2/AxewBlackBolt145.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Fraxure','146/086',1,'Dragon','Illustration Rare','https://archives.bulbagarden.net/media/upload/8/85/FraxureBlackBolt146.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Haxorus','147/086',1,'Dragon','Illustration Rare','https://archives.bulbagarden.net/media/upload/d/da/HaxorusBlackBolt147.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Pidove','148/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/f4/PidoveBlackBolt148.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Tranquill','149/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/4/4f/TranquillBlackBolt149.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Unfezant','150/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/e/eb/UnfezantBlackBolt150.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Audino','151/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/a/a2/AudinoBlackBolt151.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Minccino','152/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/e/ee/MinccinoBlackBolt152.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Cinccino','153/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/e/e1/CinccinoBlackBolt153.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Rufflet','154/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/8/84/RuffletBlackBolt154.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Braviary','155/086',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/f/fa/BraviaryBlackBolt155.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Serperior ex','156/086',1,'Grass','Ultra Rare','https://archives.bulbagarden.net/media/upload/b/b3/SerperiorexBlackBolt156.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Kyurem ex','157/086',1,'Water','Ultra Rare','https://archives.bulbagarden.net/media/upload/d/de/KyuremexBlackBolt157.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Zekrom ex','158/086',1,'Lightning','Ultra Rare','https://archives.bulbagarden.net/media/upload/e/e0/ZekromexBlackBolt158.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Meloetta ex','159/086',1,'Psychic','Ultra Rare','https://archives.bulbagarden.net/media/upload/5/5b/MeloettaexBlackBolt159.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Excadrill ex','160/086',1,'Fighting','Ultra Rare','https://archives.bulbagarden.net/media/upload/8/82/ExcadrillexBlackBolt160.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Genesect ex','161/086',1,'Metal','Ultra Rare','https://archives.bulbagarden.net/media/upload/d/df/GenesectexBlackBolt161.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Fennel','162/086',1,'Trainer','Ultra Rare','https://archives.bulbagarden.net/media/upload/b/b2/FennelBlackBolt162.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','N''s Plan','163/086',1,'Trainer','Ultra Rare','https://archives.bulbagarden.net/media/upload/a/ac/NPlanBlackBolt163.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Serperior ex','164/086',1,'Grass','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/a/ae/SerperiorexBlackBolt164.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Kyurem ex','165/086',1,'Water','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/3/37/KyuremexBlackBolt165.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Zekrom ex','166/086',1,'Lightning','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/a/ab/ZekromexBlackBolt166.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Meloetta ex','167/086',1,'Psychic','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/2/2c/MeloettaexBlackBolt167.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Excadrill ex','168/086',1,'Fighting','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/d/db/ExcadrillexBlackBolt168.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Genesect ex','169/086',1,'Metal','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/d/da/GenesectexBlackBolt169.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','N''s Plan','170/086',1,'Trainer','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/0/07/NPlanBlackBolt170.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Victini','171/086',1,'Fire','Black White Rare','https://archives.bulbagarden.net/media/upload/9/9f/VictiniBlackBolt171.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Black Bolt','Zekrom ex','172/086',1,'Lightning','Black White Rare','https://archives.bulbagarden.net/media/upload/0/07/ZekromexBlackBolt172.jpg');

--===== Journey Together cards =====

INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Journey Together','Caterpie','001/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/e/e7/CaterpieJourneyTogether1.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Journey Together','Metapod','002/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/5/51/MetapodJourneyTogether2.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Journey Together','Butterfree','003/159',1,'Grass','Rare','https://archives.bulbagarden.net/media/upload/4/4f/ButterfreeJourneyTogether3.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Journey Together','Paras','004/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/e/ed/ParasJourneyTogether4.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Journey Together','Parasect','005/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/8/87/ParasectJourneyTogether5.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Petilil','006/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/thumb/4/40/PetililJourneyTogether6.jpg/180px-PetililJourneyTogether6.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lilligant','007/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/6/67/LilligantJourneyTogether7.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Maractus','008/159',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/6/61/MaractusJourneyTogether8.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Karrablast','009/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/8/8e/KarrablastJourneyTogether9.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Foongus','010/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/d/dc/FoongusJourneyTogether10.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Amoongussex','011/159',1,'Grass','Double Rare','https://archives.bulbagarden.net/media/upload/d/d1/AmoongussexJourneyTogether11.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Shelmet','012/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/c/cc/ShelmetJourneyTogether12.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Accelgor','013/159',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/f/fe/AccelgorJourneyTogether13.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Durant','014/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/f/f6/DurantJourneyTogether14.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Virizion','015/159',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/b/b2/VirizionJourneyTogether15.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Sprigatito','016/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/6/6f/SprigatitoJourneyTogether16.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Floragato','017/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/d/d9/FloragatoJourneyTogether17.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Meowscarada','018/159',1,'Grass','Rare','https://archives.bulbagarden.net/media/upload/1/12/MeowscaradaJourneyTogether18.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Nymble','019/159',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/0/05/NymbleJourneyTogether19.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Magmar','020/159',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/1/1c/MagmarJourneyTogether20.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Magmortar','021/159',1,'Fire','Rare','https://archives.bulbagarden.net/media/upload/1/17/MagmortarJourneyTogether21.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Torchic','022/159',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/2/27/TorchicJourneyTogether22.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Combusken','023/159',1,'Fire','Uncommon','https://archives.bulbagarden.net/media/upload/b/bb/CombuskenJourneyTogether23.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Blazikenex','024/159',1,'Fire','Double Rare','https://archives.bulbagarden.net/media/upload/4/4b/BlazikenexJourneyTogether24.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Torkoal','025/159',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/a/ad/TorkoalJourneyTogether25.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Darumaka','026/159',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/f/f1/NDarumakaJourneyTogether26.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Darmanitan','027/159',1,'Fire','Uncommon','https://archives.bulbagarden.net/media/upload/0/04/NDarmanitanJourneyTogether27.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Larvesta','028/159',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/7/7c/LarvestaJourneyTogether28.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Volcarona','029/159',1,'Fire','Uncommon','https://archives.bulbagarden.net/media/upload/f/f3/VolcaronaJourneyTogether29.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Reshiramex','030/159',1,'Fire','Double Rare','https://archives.bulbagarden.net/media/upload/a/a7/ReshiramexJourneyTogether30.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Volcanionex','031/159',1,'Fire','Double Rare','https://archives.bulbagarden.net/media/upload/6/6d/VolcanionexJourneyTogether31.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Articuno','032/159',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/c/c4/ArticunoJourneyTogether32.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Remoraid','033/159',1,'Water','Common','https://archives.bulbagarden.net/media/upload/e/e9/RemoraidJourneyTogether33.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Octillery','034/159',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/4/4f/OctilleryJourneyTogether34.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lotad','035/159',1,'Water','Common','https://archives.bulbagarden.net/media/upload/9/96/LotadJourneyTogether35.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lombre','036/159',1,'Water','Common','https://archives.bulbagarden.net/media/upload/a/a2/LombreJourneyTogether36.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Ludicolo','037/159',1,'Water','Rare','https://archives.bulbagarden.net/media/upload/7/7a/LudicoloJourneyTogether37.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Wingull','038/159',1,'Water','Common','https://archives.bulbagarden.net/media/upload/7/71/WingullJourneyTogether38.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Pelipper','039/159',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/2/26/PelipperJourneyTogether39.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Wailmer','040/159',1,'Water','Common','https://archives.bulbagarden.net/media/upload/7/7c/WailmerJourneyTogether40.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Wailord','041/159',1,'Water','Rare','https://archives.bulbagarden.net/media/upload/d/db/WailordJourneyTogether41.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Regice','042/159',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/8/80/RegiceJourneyTogether42.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Veluzaex','043/159',1,'Water','Double Rare','https://archives.bulbagarden.net/media/upload/0/09/VeluzaexJourneyTogether43.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Alolan Geodude','044/159',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/9/96/AlolanGeodudeJourneyTogether44.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Alolan Graveler','045/159',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/6/6e/AlolanGravelerJourneyTogether45.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Alolan Golem','046/159',1,'Lightning','Uncommon','https://archives.bulbagarden.net/media/upload/9/98/AlolanGolemJourneyTogether46.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Voltorb','047/159',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/4/47/IonoVoltorbJourneyTogether47.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Electrode','048/159',1,'Lightning','Uncommon','https://archives.bulbagarden.net/media/upload/4/41/IonoElectrodeJourneyTogether48.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Joltik','049/159',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/8/87/NJoltikJourneyTogether49.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Togedemaru','050/159',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/2/25/TogedemaruJourneyTogether50.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Tapu Kokoex','051/159',1,'Lightning','Double Rare','https://archives.bulbagarden.net/media/upload/3/3b/TapuKokoexJourneyTogether51.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Tadbulb','052/159',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/0/0f/IonoTadbulbJourneyTogether52.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Belliboltex','053/159',1,'Lightning','Double Rare','https://archives.bulbagarden.net/media/upload/e/e0/IonoBelliboltexJourneyTogether53.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Wattrel','054/159',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/0/0d/IonoWattrelJourneyTogether54.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Kilowattrel','055/159',1,'Lightning','Rare','https://archives.bulbagarden.net/media/upload/6/62/IonoKilowattrelJourneyTogether55.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Clefairyex','056/159',1,'Psychic','Double Rare','https://archives.bulbagarden.net/media/upload/9/99/LillieClefairyexJourneyTogether56.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Alolan Marowak','057/159',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/2/22/AlolanMarowakJourneyTogether57.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Mr. Mime','058/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/0/09/MrMimeJourneyTogether58.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Shuppet','059/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/thumb/1/12/ShuppetJourneyTogether59.jpg/180px-ShuppetJourneyTogether59.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Banette','060/159',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/d/d2/BanetteJourneyTogether60.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Beldum','061/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/e/e2/BeldumJourneyTogether61.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Metang','062/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/9/92/MetangJourneyTogether62.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Metagross','063/159',1,'Psychic','Rare','https://archives.bulbagarden.net/media/upload/4/44/MetagrossJourneyTogether63.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Sigilyph','064/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/1/16/NSigilyphJourneyTogether64.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Oricorio','065/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/d/da/OricorioJourneyTogether65.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Cutiefly','066/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/5/58/LillieCutieflyJourneyTogether66.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Ribombee','067/159',1,'Psychic','Rare','https://archives.bulbagarden.net/media/upload/8/8e/LillieRibombeeJourneyTogether67.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Comfey','068/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/9/9f/LillieComfeyJourneyTogether68.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Mimikyuex','069/159',1,'Psychic','Double Rare','https://archives.bulbagarden.net/media/upload/d/dc/MimikyuexJourneyTogether69.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Dhelmise','070/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/f/f6/DhelmiseJourneyTogether70.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Impidimp','071/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/6/6c/ImpidimpJourneyTogether71.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Morgrem','072/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/6/6f/MorgremJourneyTogether72.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Grimmsnarl','073/159',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/0/0f/GrimmsnarlJourneyTogether73.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Milcery','074/159',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/7/77/MilceryJourneyTogether74.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Alcremieex','075/159',1,'Psychic','Double Rare','https://archives.bulbagarden.net/media/upload/d/de/AlcremieexJourneyTogether75.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Cubone','076/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/9/94/CuboneJourneyTogether76.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Swinub','077/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/1/1a/SwinubJourneyTogether77.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Piloswine','078/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/e/e9/PiloswineJourneyTogether78.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Mamoswineex','079/159',1,'Fighting','Double Rare','https://archives.bulbagarden.net/media/upload/3/34/MamoswineexJourneyTogether79.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Larvitar','080/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/1/17/LarvitarJourneyTogether80.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Pupitar','081/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/e/ed/PupitarJourneyTogether81.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Regirock','082/159',1,'Fighting','Rare','https://archives.bulbagarden.net/media/upload/9/99/RegirockJourneyTogether82.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Pancham','083/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/c/c7/PanchamJourneyTogether83.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Rockruff','084/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/thumb/a/ae/RockruffJourneyTogether84.jpg/180px-RockruffJourneyTogether84.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lycanroc','085/159',1,'Fighting','Rare','https://archives.bulbagarden.net/media/upload/1/1d/LycanrocJourneyTogether85.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Silicobra','086/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/e/ee/HopSilicobraJourneyTogether86.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Sandaconda','087/159',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/8/84/HopSandacondaJourneyTogether87.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Toedscool','088/159',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/7/76/ToedscoolJourneyTogether88.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Toedscruel','089/159',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/4/45/ToedscruelJourneyTogether89.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Klawf','090/159',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/a/a8/KlawfJourneyTogether90.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Koffing','091/159',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/a/a4/KoffingJourneyTogether91.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Weezing','092/159',1,'Darkness','Uncommon','https://archives.bulbagarden.net/media/upload/e/ea/WeezingJourneyTogether92.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Paldean Wooper','093/159',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/2/23/PaldeanWooperJourneyTogether93.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Paldean Clodsireex','094/159',1,'Darkness','Double Rare','https://archives.bulbagarden.net/media/upload/5/58/PaldeanClodsireexJourneyTogether94.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Tyranitar','095/159',1,'Darkness','Rare','https://archives.bulbagarden.net/media/upload/c/c5/TyranitarJourneyTogether95.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Purrloin','096/159',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/f/ff/NPurrloinJourneyTogether96.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Zorua','097/159',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/1/12/NZoruaJourneyTogether97.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Zoroarkex','098/159',1,'Darkness','Double Rare','https://archives.bulbagarden.net/media/upload/d/d5/NZoroarkexJourneyTogether98.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Pangoro','099/159',1,'Darkness','Uncommon','https://archives.bulbagarden.net/media/upload/6/6f/PangoroJourneyTogether99.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lokix','100/159',1,'Darkness','Uncommon','https://archives.bulbagarden.net/media/upload/f/f9/LokixJourneyTogether100.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Bombirdier','101/159',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/1/13/BombirdierJourneyTogether101.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Escavalier','102/159',1,'Metal','Uncommon','https://archives.bulbagarden.net/media/upload/3/31/EscavalierJourneyTogether102.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Klink','103/159',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/0/09/NKlinkJourneyTogether103.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Klang','104/159',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/c/c7/NKlangJourneyTogether104.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Klinklang','105/159',1,'Metal','Uncommon','https://archives.bulbagarden.net/media/upload/a/a0/NKlinklangJourneyTogether105.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Galarian Stunfisk','106/159',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/1/14/GalarianStunfiskJourneyTogether106.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Magearna','107/159',1,'Metal','Rare','https://archives.bulbagarden.net/media/upload/b/bb/MagearnaJourneyTogether107.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Corviknight','108/159',1,'Metal','Uncommon','https://archives.bulbagarden.net/media/upload/7/70/HopCorviknightJourneyTogether108.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Cufant','109/159',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/thumb/5/5b/CufantJourneyTogether109.jpg/180px-CufantJourneyTogether109.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Copperajah','110/159',1,'Metal','Uncommon','https://archives.bulbagarden.net/media/upload/d/d6/CopperajahJourneyTogether110.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Zacianex','111/159',1,'Metal','Double Rare','https://archives.bulbagarden.net/media/upload/9/9e/HopZacianexJourneyTogether111.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Bagon','112/159',1,'Dragon','Common','https://archives.bulbagarden.net/media/upload/5/5b/BagonJourneyTogether112.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Shelgon','113/159',1,'Dragon','Common','https://archives.bulbagarden.net/media/upload/f/fc/ShelgonJourneyTogether113.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Salamenceex','114/159',1,'Dragon','Double Rare','https://archives.bulbagarden.net/media/upload/d/d6/SalamenceexJourneyTogether114.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Druddigon','115/159',1,'Dragon','Common','https://archives.bulbagarden.net/media/upload/d/d8/DruddigonJourneyTogether115.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Reshiram','116/159',1,'Dragon','Rare','https://archives.bulbagarden.net/media/upload/8/84/NReshiramJourneyTogether116.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Snorlax','117/159',1,'Colorless','Rare','https://archives.bulbagarden.net/media/upload/thumb/4/43/HopSnorlaxJourneyTogether117.jpg/180px-HopSnorlaxJourneyTogether117.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Sentret','118/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/thumb/7/72/SentretJourneyTogether118.jpg/180px-SentretJourneyTogether118.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Furret','119/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/2/25/FurretJourneyTogether119.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Dunsparce','120/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/d/d0/DunsparceJourneyTogether120.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Dudunsparceex','121/159',1,'Colorless','Double Rare','https://archives.bulbagarden.net/media/upload/1/1f/DudunsparceexJourneyTogether121.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Kecleon','122/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/c/c7/KecleonJourneyTogether122.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Tropius','123/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/4/4f/TropiusJourneyTogether123.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Audino','124/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/thumb/e/ea/AudinoJourneyTogether124.jpg/180px-AudinoJourneyTogether124.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Minccino','125/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/thumb/9/93/MinccinoJourneyTogether125.jpg/180px-MinccinoJourneyTogether125.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Cinccino','126/159',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/f/f3/CinccinoJourneyTogether126.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Noibat','127/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/f/f1/NoibatJourneyTogether127.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Noivern','128/159',1,'Colorless','Rare','https://archives.bulbagarden.net/media/upload/3/30/NoivernJourneyTogether128.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Komala','129/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/c/c0/KomalaJourneyTogether129.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Drampa','130/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/e/ee/DrampaJourneyTogether130.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Skwovet','131/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/5/58/SkwovetJourneyTogether131.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Greedent','132/159',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/5/56/GreedentJourneyTogether132.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Rookidee','133/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/1/18/HopRookideeJourneyTogether133.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Corvisquire','134/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/5/5e/HopCorvisquireJourneyTogether134.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Wooloo','135/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/2/22/HopWoolooJourneyTogether135.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Dubwool','136/159',1,'Colorless','Rare','https://archives.bulbagarden.net/media/upload/0/0f/HopDubwoolJourneyTogether136.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Cramorant','137/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/f/f7/CramorantJourneyTogether137.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Cramorant','138/159',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/1/16/HopCramorantJourneyTogether138.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lechonk','139/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/a/af/LechonkJourneyTogether139.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Oinkologne','140/159',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/4/43/OinkologneJourneyTogether140.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Squawkabilly','141/159',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/2/2c/SquawkabillyJourneyTogether141.jpg');

INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Billy & O''Nare','142/159',1,'Su','Common','https://archives.bulbagarden.net/media/upload/a/a8/BillyO%27NareJourneyTogether142.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Black Belt''s Training','143/159',1,'Su','Common','https://archives.bulbagarden.net/media/upload/7/7a/BlackBeltTrainingJourneyTogether143.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Black Belt''s Training','144/159',1,'Su','Common','https://archives.bulbagarden.net/media/upload/e/ea/BlackBeltTrainingJourneyTogether144.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Black Belt''s Training','145/159',1,'Su','Common','https://archives.bulbagarden.net/media/upload/6/6f/BlackBeltTrainingJourneyTogether145.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Brock''s Scouting','146/159',1,'Su','Uncommon','https://archives.bulbagarden.net/media/upload/2/29/BrockScoutingJourneyTogether146.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Bag','147/159',1,'I','Uncommon','https://archives.bulbagarden.net/media/upload/b/b9/HopBagJourneyTogether147.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Choice Band','148/159',1,'PT','Uncommon','https://archives.bulbagarden.net/media/upload/c/cd/HopChoiceBandJourneyTogether148.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iris''s Fighting Spirit','149/159',1,'Su','Uncommon','https://archives.bulbagarden.net/media/upload/c/cb/IrisFightingSpiritJourneyTogether149.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Levincia','150/159',1,'St','Uncommon','https://archives.bulbagarden.net/media/upload/8/86/LevinciaJourneyTogether150.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Pearl','151/159',1,'PT','Uncommon','https://archives.bulbagarden.net/media/upload/f/fd/LilliePearlJourneyTogether151.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Castle','152/159',1,'St','Uncommon','https://archives.bulbagarden.net/media/upload/e/e2/NCastleJourneyTogether152.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s PP Up','153/159',1,'I','Uncommon','https://archives.bulbagarden.net/media/upload/3/35/NPPUpJourneyTogether153.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Postwick','154/159',1,'St','Uncommon','https://archives.bulbagarden.net/media/upload/2/27/PostwickJourneyTogether154.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Professor''s Research [Professor Sada]','155/159',1,'Su','Common','https://archives.bulbagarden.net/media/upload/a/a2/ProfessorResearchJourneyTogether155.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Redeemable Ticket','156/159',1,'I','Uncommon','https://archives.bulbagarden.net/media/upload/3/31/RedeemableTicketJourneyTogether156.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Ruffian','157/159',1,'Su','Uncommon','https://archives.bulbagarden.net/media/upload/b/b9/RuffianJourneyTogether157.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Super Potion','158/159',1,'I','Uncommon','https://archives.bulbagarden.net/media/upload/6/66/SuperPotionJourneyTogether158.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Spiky Energy','159/159',1,'Colorless E','Uncommon','https://archives.bulbagarden.net/media/upload/0/09/SpikyEnergyJourneyTogether159.jpg');

-- Illustration Rares and higher numbers
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Maractus','160/159',1,'Grass','Illustration Rare','https://archives.bulbagarden.net/media/upload/2/22/MaractusJourneyTogether160.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Articuno','161/159',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/4/4b/ArticunoJourneyTogether161.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Wailord','162/159',1,'Water','Illustration Rare','https://archives.bulbagarden.net/media/upload/0/07/WailordJourneyTogether162.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Kilowattrel','163/159',1,'Lightning','Illustration Rare','https://archives.bulbagarden.net/media/upload/1/1c/IonoKilowattrelJourneyTogether163.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Ribombee','164/159',1,'Psychic','Illustration Rare','https://archives.bulbagarden.net/media/upload/3/3f/LillieRibombeeJourneyTogether164.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Swinub','165/159',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/5/51/SwinubJourneyTogether165.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lycanroc','166/159',1,'Fighting','Illustration Rare','https://archives.bulbagarden.net/media/upload/d/d0/LycanrocJourneyTogether166.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Reshiram','167/159',1,'Dragon','Illustration Rare','https://archives.bulbagarden.net/media/upload/2/22/NReshiramJourneyTogether167.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Furret','168/159',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/2/2e/FurretJourneyTogether168.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Noibat','169/159',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/0/0f/NoibatJourneyTogether169.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Wooloo','170/159',1,'Colorless','Illustration Rare','https://archives.bulbagarden.net/media/upload/e/e6/HopWoolooJourneyTogether170.jpg');

-- Ultra Rares
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Volcanionex','171/159',1,'Fire','Ultra Rare','https://archives.bulbagarden.net/media/upload/2/2b/VolcanionexJourneyTogether171.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Belliboltex','172/159',1,'Lightning','Ultra Rare','https://archives.bulbagarden.net/media/upload/5/56/IonoBelliboltexJourneyTogether172.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Clefairyex','173/159',1,'Psychic','Ultra Rare','https://archives.bulbagarden.net/media/upload/2/29/LillieClefairyexJourneyTogether173.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Mamoswineex','174/159',1,'Fighting','Ultra Rare','https://archives.bulbagarden.net/media/upload/4/4f/MamoswineexJourneyTogether174.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Zoroarkex','175/159',1,'Darkness','Ultra Rare','https://archives.bulbagarden.net/media/upload/d/dc/NZoroarkexJourneyTogether175.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Zacianex','176/159',1,'Metal','Ultra Rare','https://archives.bulbagarden.net/media/upload/e/ea/HopZacianexJourneyTogether176.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Salamenceex','177/159',1,'Dragon','Ultra Rare','https://archives.bulbagarden.net/media/upload/e/e0/SalamenceexJourneyTogether177.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Dudunsparceex','178/159',1,'Colorless','Ultra Rare','https://archives.bulbagarden.net/media/upload/2/25/DudunsparceexJourneyTogether178.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Brock''s Scouting','179/159',1,'Su','Ultra Rare','https://archives.bulbagarden.net/media/upload/a/a6/BrockScoutingJourneyTogether179.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iris''s Fighting Spirit','180/159',1,'Su','Ultra Rare','https://archives.bulbagarden.net/media/upload/c/c0/IrisFightingSpiritJourneyTogether180.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Ruffian','181/159',1,'Su','Ultra Rare','https://archives.bulbagarden.net/media/upload/5/56/RuffianJourneyTogether181.jpg');

-- Special Illustration Rares
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Volcanionex','182/159',1,'Fire','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/d/dd/VolcanionexJourneyTogether182.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Belliboltex','183/159',1,'Lightning','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/a/a9/IonoBelliboltexJourneyTogether183.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Lillie''s Clefairyex','184/159',1,'Psychic','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/b/b5/LillieClefairyexJourneyTogether184.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Zoroarkex','185/159',1,'Darkness','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/d/d3/NZoroarkexJourneyTogether185.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Hop''s Zacianex','186/159',1,'Metal','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/c/ce/HopZacianexJourneyTogether186.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Salamenceex','187/159',1,'Dragon','Special Illustration Rare','https://archives.bulbagarden.net/media/upload/e/e9/SalamenceexJourneyTogether187.jpg');

-- Hyper Rares
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Iono''s Belliboltex','188/159',1,'Lightning','Hyper Rare','https://archives.bulbagarden.net/media/upload/9/97/IonoBelliboltexJourneyTogether188.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','N''s Zoroarkex','189/159',1,'Darkness','Hyper Rare','https://archives.bulbagarden.net/media/upload/5/58/NZoroarkexJourneyTogether189.jpg');
INSERT INTO cards (pack, name, english_no, variant_index,type,rarity,image_url) VALUES ('Journey Together','Spiky Energy','190/159',1,'Colorless E','Hyper Rare','https://archives.bulbagarden.net/media/upload/7/72/SpikyEnergyJourneyTogether190.jpg');

-- ===== Stormfront cards =====

INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Dusknoir','001/100',1,'Psychic','Rare Holo','https://archives.bulbagarden.net/media/upload/1/16/DusknoirStormfront1.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Empoleon','002/100',1,'Metal','Rare Holo','https://archives.bulbagarden.net/media/upload/e/e1/EmpoleonStormfront2.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Infernape','003/100',1,'Fighting','Rare Holo','https://archives.bulbagarden.net/media/upload/f/fa/InfernapeStormfront3.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Lumineon','004/100',1,'Water','Rare Holo','https://archives.bulbagarden.net/media/upload/thumb/4/43/LumineonStormfront4.jpg/180px-LumineonStormfront4.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Magnezone','005/100',1,'Metal','Rare Holo','https://archives.bulbagarden.net/media/upload/8/8a/MagnezoneStormfront5.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Magnezone','006/100',1,'Lightning','Rare Holo','https://archives.bulbagarden.net/media/upload/c/c1/MagnezoneStormfront6.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Mismagius','007/100',1,'Psychic','Rare Holo','https://archives.bulbagarden.net/media/upload/7/71/MismagiusStormfront7.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Raichu','008/100',1,'Lightning','Rare Holo','https://archives.bulbagarden.net/media/upload/2/24/RaichuStormfront8.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Regigigas','009/100',1,'Colorless','Rare Holo','https://archives.bulbagarden.net/media/upload/d/d9/RegigigasStormfront9.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Sceptile','010/100',1,'Grass','Rare Holo','https://archives.bulbagarden.net/media/upload/b/b8/SceptileStormfront10.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Torterra','011/100',1,'Fighting','Rare Holo','https://archives.bulbagarden.net/media/upload/e/ee/TorterraStormfront11.jpg');

INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Abomasnow','012/100',1,'Water','Rare','https://archives.bulbagarden.net/media/upload/thumb/0/03/AbomasnowStormfront12.jpg/180px-AbomasnowStormfront12.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Bronzong','013/100',1,'Psychic','Rare','https://archives.bulbagarden.net/media/upload/1/14/BronzongStormfront13.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Cherrim','014/100',1,'Grass','Rare','https://archives.bulbagarden.net/media/upload/0/08/CherrimStormfront14.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Drapion','015/100',1,'Darkness','Rare','https://archives.bulbagarden.net/media/upload/9/9f/DrapionStormfront15.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Drifblim','016/100',1,'Psychic','Rare','https://archives.bulbagarden.net/media/upload/thumb/8/8e/DrifblimStormfront16.jpg/180px-DrifblimStormfront16.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Dusknoir','017/100',1,'Psychic','Rare','https://archives.bulbagarden.net/media/upload/thumb/2/21/DusknoirStormfront17.jpg/180px-DusknoirStormfront17.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Gengar','018/100',1,'Psychic','Rare','https://archives.bulbagarden.net/media/upload/c/cc/GengarStormfront18.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Gyarados','019/100',1,'Water','Rare','https://archives.bulbagarden.net/media/upload/7/70/GyaradosStormfront19.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Machamp','020/100',1,'Fighting','Rare','https://archives.bulbagarden.net/media/upload/9/9b/MachampStormfront20.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Mamoswine','021/100',1,'Fighting','Rare','https://archives.bulbagarden.net/media/upload/thumb/7/7d/MamoswineStormfront21.jpg/180px-MamoswineStormfront21.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Rapidash','022/100',1,'Fire','Rare','https://archives.bulbagarden.net/media/upload/b/b2/RapidashStormfront22.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Roserade','023/100',1,'Psychic','Rare','https://archives.bulbagarden.net/media/upload/e/e0/RoseradeStormfront23.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Salamence','024/100',1,'Colorless','Rare','https://archives.bulbagarden.net/media/upload/2/2b/SalamenceStormfront24.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Scizor','025/100',1,'Grass','Rare','https://archives.bulbagarden.net/media/upload/c/c4/ScizorStormfront25.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Skuntank','026/100',1,'Darkness','Rare','https://archives.bulbagarden.net/media/upload/thumb/d/d7/SkuntankStormfront26.jpg/180px-SkuntankStormfront26.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Staraptor','027/100',1,'Colorless','Rare','https://archives.bulbagarden.net/media/upload/3/3a/StaraptorStormfront27.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Steelix','028/100',1,'Metal','Rare','https://archives.bulbagarden.net/media/upload/thumb/d/da/SteelixStormfront28.jpg/800px-SteelixStormfront28.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Tangrowth','029/100',1,'Grass','Rare','https://archives.bulbagarden.net/media/upload/3/32/TangrowthStormfront29.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Tyranitar','030/100',1,'Darkness','Rare','https://archives.bulbagarden.net/media/upload/4/45/TyranitarStormfront30.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Vespiquen','031/100',1,'Grass','Rare','https://archives.bulbagarden.net/media/upload/thumb/6/68/VespiquenStormfront31.jpg/180px-VespiquenStormfront31.jpg');

INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Bibarel','032/100',1,'Water','Uncommon','https://archives.bulbagarden.net/media/upload/8/8a/BibarelStormfront32.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Budew','033/100',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/3/3d/BudewStormfront33.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Dusclops','034/100',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/e/e4/DusclopsStormfront34.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Dusclops','035/100',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/8/8d/DusclopsStormfront35.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Electrode','036/100',1,'Lightning','Uncommon','https://archives.bulbagarden.net/media/upload/2/26/ElectrodeStormfront36.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Electrode','037/100',1,'Lightning','Uncommon','https://archives.bulbagarden.net/media/upload/0/0d/ElectrodeStormfront37.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Farfetch''d','038/100',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/9/9c/Farfetch%27dStormfront38.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Grovyle','039/100',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/4/40/GrovyleStormfront39.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Haunter','040/100',1,'Psychic','Uncommon','https://archives.bulbagarden.net/media/upload/thumb/e/e3/HaunterStormfront40.jpg/180px-HaunterStormfront40.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Machoke','041/100',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/thumb/e/ee/MachokeStormfront41.jpg/180px-MachokeStormfront41.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Magneton','042/100',1,'Metal','Uncommon',"https://archives.bulbagarden.net/media/upload/b/b4/MagnetonStormfront42.jpg");
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Magneton','043/100',1,'Lightning','Uncommon',"https://archives.bulbagarden.net/media/upload/7/75/MagnetonStormfront43.jpg");
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Miltank','044/100',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/1/19/MiltankStormfront44.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Pichu','045/100',1,'Lightning','Uncommon','https://archives.bulbagarden.net/media/upload/9/95/PichuStormfront45.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Piloswine','046/100',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/e/e5/PiloswineStormfront46.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Pupitar','047/100',1,'Fighting','Uncommon','https://archives.bulbagarden.net/media/upload/thumb/7/7b/PupitarStormfront47.jpg/180px-PupitarStormfront47.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Sableye','048/100',1,'Darkness','Uncommon','https://archives.bulbagarden.net/media/upload/d/dd/SableyeStormfront48.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Scyther','049/100',1,'Grass','Uncommon','https://archives.bulbagarden.net/media/upload/3/34/ScytherStormfront49.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Shelgon','050/100',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/c/c6/ShelgonStormfront50.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Skarmory','051/100',1,'Metal','Uncommon','https://archives.bulbagarden.net/media/upload/thumb/c/cb/SkarmoryStormfront51.jpg/180px-SkarmoryStormfront51.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Staravia','052/100',1,'Colorless','Uncommon','https://archives.bulbagarden.net/media/upload/9/98/StaraviaStormfront52.jpg');

INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Bagon','053/100',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/a/a8/BagonStormfront53.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Bidoof','054/100',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/0/06/BidoofStormfront54.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Bronzor','055/100',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/thumb/c/c4/BronzorStormfront55.jpg/180px-BronzorStormfront55.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Cherubi','056/100',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/0/05/CherubiStormfront56.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Combee','057/100',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/e/e7/CombeeStormfront57.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Drifloon','058/100',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/thumb/a/a9/DrifloonStormfront58.jpg/180px-DrifloonStormfront58.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Duskull','059/100',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/0/02/DuskullStormfront59.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Duskull','060/100',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/3/3a/DuskullStormfront60.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Finneon','061/100',1,'Water','Common','https://archives.bulbagarden.net/media/upload/8/84/FinneonStormfront61.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Gastly','062/100',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/5/52/GastlyStormfront62.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Larvitar','063/100',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/thumb/6/6d/LarvitarStormfront63.jpg/180px-LarvitarStormfront63.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Machop','064/100',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/8/84/MachopStormfront64.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Magikarp','065/100',1,'Water','Common','https://archives.bulbagarden.net/media/upload/f/f5/MagikarpStormfront65.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Magnemite','066/100',1,'Metal','Common','https://archives.bulbagarden.net/media/upload/b/bf/MagnemiteStormfront66.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Magnemite','067/100',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/b/b2/MagnemiteStormfront67.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Misdreavus','068/100',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/6/67/MisdreavusStormfront68.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Onix','069/100',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/b/ba/OnixStormfront69.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Pikachu','070/100',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/7/79/PikachuStormfront70.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Ponyta','071/100',1,'Fire','Common','https://archives.bulbagarden.net/media/upload/a/a9/PonytaStormfront71.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Roselia','072/100',1,'Psychic','Common','https://archives.bulbagarden.net/media/upload/4/47/RoseliaStormfront72.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Skorupi','073/100',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/2/25/SkorupiStormfront73.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Snover','074/100',1,'Water','Common','https://archives.bulbagarden.net/media/upload/c/ca/SnoverStormfront74.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Starly','075/100',1,'Colorless','Common','https://archives.bulbagarden.net/media/upload/thumb/2/2f/StarlyStormfront75.jpg/180px-StarlyStormfront75.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Stunky','076/100',1,'Darkness','Common','https://archives.bulbagarden.net/media/upload/0/0a/StunkyStormfront76.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Swinub','077/100',1,'Fighting','Common','https://archives.bulbagarden.net/media/upload/0/09/SwinubStormfront77.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Tangela','078/100',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/7/74/TangelaStormfront78.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Treecko','079/100',1,'Grass','Common','https://archives.bulbagarden.net/media/upload/8/84/TreeckoStormfront79.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Voltorb','080/100',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/thumb/7/73/VoltorbStormfront80.jpg/180px-VoltorbStormfront80.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Voltorb','081/100',1,'Lightning','Common','https://archives.bulbagarden.net/media/upload/7/72/VoltorbStormfront81.jpg');

-- Trainers / Stadiums / Supporters / Energies
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Conductive Quarry','082/100',1,'St','Uncommon','https://archives.bulbagarden.net/media/upload/a/ac/ConductiveQuarryStormfront82.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Energy Link','083/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/4/4f/EnergyLinkStormfront83.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Energy Switch','084/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/thumb/b/b1/EnergySwitchAquapolis120.jpg/800px-EnergySwitchAquapolis120.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Great Ball','085/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/5/55/GreatBallSunMoon119.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Luxury Ball','086/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/4/4c/LuxuryBallStormfront86.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Marley''s Request','087/100',1,'Su','Uncommon','https://archives.bulbagarden.net/media/upload/d/db/MarleyRequestStormfront87.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Poké Blower +','088/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/0/0c/Pok%C3%A9BlowerStormfront88.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Poké Drawer +','089/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/f/f4/Pok%C3%A9DrawerStormfront89.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Poké Healer +','090/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/1/17/Pok%C3%A9HealerStormfront90.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Premier Ball','091/100',1,'T','Uncommon','https://archives.bulbagarden.net/media/upload/1/16/PremierBallGreatEncounters101.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Potion','092/100',1,'T','Common','https://archives.bulbagarden.net/media/upload/1/1e/PotionSecretWonders127.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Switch','093/100',1,'T','Common','https://archives.bulbagarden.net/media/upload/0/02/SwitchSunMoon160.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Cyclone Energy','094/100',1,'Colorless E','Uncommon','https://archives.bulbagarden.net/media/upload/d/d1/CycloneEnergySkyridge143.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Warp Energy','095/100',1,'Colorless E','Uncommon','https://archives.bulbagarden.net/media/upload/f/f2/WarpEnergyPPromo41.jpg');

-- LV.X and Secret Rares
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Dusknoir LV.X','096/100',1,'Psychic','Rare Holo LV.X','https://archives.bulbagarden.net/media/upload/d/d3/DusknoirLVXStormfront96.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Heatran LV.X','097/100',1,'Fire','Rare Holo LV.X','https://archives.bulbagarden.net/media/upload/thumb/7/7d/HeatranLVXStormfront97.jpg/180px-HeatranLVXStormfront97.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Machamp LV.X','098/100',1,'Fighting','Rare Holo LV.X','https://archives.bulbagarden.net/media/upload/c/c7/MachampLVXStormfront98.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Raichu LV.X','099/100',1,'Lightning','Rare Holo LV.X','https://archives.bulbagarden.net/media/upload/2/27/RaichuLVXStormfront99.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Regigigas LV.X','100/100',1,'Colorless','Rare Holo LV.X','https://archives.bulbagarden.net/media/upload/thumb/a/aa/RegigigasLVXDPPromo30.jpg/800px-RegigigasLVXDPPromo30.jpg');

INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Charmander','101/100',1,'Fire','Rare Secret','https://archives.bulbagarden.net/media/upload/b/be/CharmanderStormfront101.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Charmeleon','102/100',1,'Fire','Rare Secret','https://archives.bulbagarden.net/media/upload/6/63/CharmeleonStormfront102.jpg');
INSERT INTO cards (pack, name, english_no, variant_index, type, rarity, image_url) VALUES ('Stormfront','Charizard','103/100',1,'Fire','Rare Secret','https://archives.bulbagarden.net/media/upload/3/3b/CharizardStormfront103.jpg');

COMMIT;
