PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS cards (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pack            TEXT    NOT NULL CHECK (pack = 'Black Bolt'),
    name            TEXT    NOT NULL,
    english_no      TEXT    NOT NULL,
    variant_index   INTEGER NOT NULL DEFAULT 1,
    type            TEXT    NOT NULL,
    rarity          TEXT    NOT NULL,
    image_url       TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_cards_pack_no_variant
ON cards(pack, english_no, variant_index);

-- ===== Favorites (per guild, per user) =====
PRAGMA foreign_keys = ON;

-- One favorite per (guild_id, user_id). References cards(id).
CREATE TABLE IF NOT EXISTS user_favorite_guild (
    guild_id TEXT    NOT NULL,
    user_id  TEXT    NOT NULL,
    card_id  INTEGER NOT NULL,
    set_ts   INTEGER NOT NULL,                -- unix timestamp
    PRIMARY KEY (guild_id, user_id),
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Disallow favoriting a card the user doesn't own in that guild.
-- These triggers reference user_collection_guild (created by your Python ensure_db()).
-- It's okay if that table doesn’t exist yet as SQLite checks at runtime when the trigger fires.

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
COMMIT;
