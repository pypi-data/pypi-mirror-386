use pest::{Parser, error::Error};

use crate::{ast::DuperValue, builder::DuperBuilder};

/// The [`pest`]-based parser for Duper.
#[derive(pest_derive::Parser)]
#[grammar = "grammar.pest"]
pub struct DuperParser;

impl DuperParser {
    /// Parse a Duper trunk, i.e. only an array or object at the top level.
    ///
    /// You can map the error into a formatted `miette::Error` as follows:
    ///
    /// ```
    /// use duper::DuperParser;
    ///
    /// # let input = "{}";
    /// let duper = match DuperParser::parse_duper_trunk(input) {
    ///     Ok(duper) => duper,
    ///     Err(error) => panic!("{:?}", miette::Error::new(error.into_miette())),
    /// };
    /// ```
    pub fn parse_duper_trunk<'a>(input: &'a str) -> Result<DuperValue<'a>, Box<Error<Rule>>> {
        let mut pairs = Self::parse(Rule::duper_trunk, input)?;
        DuperBuilder::build_duper(pairs.next().unwrap())
    }

    /// Parse a Duper value at the top level.
    ///
    /// You can map the error into a formatted `miette::Error` as follows:
    ///
    /// ```
    /// use duper::DuperParser;
    ///
    /// # let input = "{}";
    /// let duper = match DuperParser::parse_duper_value(input) {
    ///     Ok(duper) => duper,
    ///     Err(error) => panic!("{:?}", miette::Error::new(error.into_miette())),
    /// };
    /// ```
    pub fn parse_duper_value<'a>(input: &'a str) -> Result<DuperValue<'a>, Box<Error<Rule>>> {
        let mut pairs = Self::parse(Rule::duper_value, input)?;
        DuperBuilder::build_duper(pairs.next().unwrap())
    }
}

#[cfg(test)]
mod duper_parser_tests {
    use crate::{
        DuperArray, DuperBytes, DuperIdentifier, DuperInner, DuperKey, DuperObject, DuperParser,
        DuperString, DuperTuple, DuperValue,
    };

    #[test]
    fn duper_trunk() {
        let input = r#"
            "hello"
        "#;
        assert!(DuperParser::parse_duper_trunk(input).is_err());

        let input = r#"
            br"¯\_(ツ)_/¯"
        "#;
        assert!(DuperParser::parse_duper_trunk(input).is_err());

        let input = r#"
            9001
        "#;
        assert!(DuperParser::parse_duper_trunk(input).is_err());

        let input = r#"
            3.14
        "#;
        assert!(DuperParser::parse_duper_trunk(input).is_err());

        let input = r#"
            true
        "#;
        assert!(DuperParser::parse_duper_trunk(input).is_err());

        let input = r#"
            null
        "#;
        assert!(DuperParser::parse_duper_trunk(input).is_err());

        let input = r#"
            (,)
        "#;
        assert!(DuperParser::parse_duper_trunk(input).is_err());

        let input = r#"
            {duper: 1337}
        "#;
        let duper = DuperParser::parse_duper_trunk(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Object(_)));

        let input = r#"
            [1, 2.2, null]
        "#;
        let duper = DuperParser::parse_duper_trunk(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Array(_)));
    }

    #[test]
    fn duper_value() {
        let input = r#"
            "hello"
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::String(_)));

        let input = r#"
            br"¯\_(ツ)_/¯"
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Bytes(_)));

        let input = r#"
            9001
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Integer(_)));

        let input = r#"
            3.14
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Float(_)));

        let input = r#"
            true
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Boolean(_)));

        let input = r#"
            null
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Null));

        let input = r#"
            (,)
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Tuple(_)));

        let input = r#"
            {duper: 1337}
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Object(_)));

        let input = r#"
            [1, 2.2, null]
        "#;
        let duper = DuperParser::parse_duper_value(input).unwrap();
        assert!(matches!(duper.inner, DuperInner::Array(_)));
    }

    #[test]
    fn example() {
        use std::borrow::Cow;

        let input = r##"
            Product({
                product_id: Uuid("1dd7b7aa-515e-405f-85a9-8ac812242609"),
                name: "Wireless Bluetooth Headphones",
                brand: "AudioTech",
                price: Decimal("129.99"),
                dimensions: (18.5, 15.2, 7.8),  // In centimeters
                weight: Kilograms(0.285),
                in_stock: true,
                specifications: {
                    battery_life: Duration("30h"),
                    noise_cancellation: true,
                    connectivity: ["Bluetooth 5.0", "3.5mm Jack"],
                },
                image_thumbnail: Png(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x64"),
                tags: ["electronics", "audio", "wireless"],
                release_date: Date("2023-11-15"),
                /* Warranty is optional */
                warranty_period: null,
                customer_ratings: {
                    latest_review: r#"Absolutely ""astounding""!! 😎"#,
                    average: 4.5,
                    count: 127,
                },
                created_at: DateTime("2023-11-17T21:50:43+00:00"),
            })
        "##;
        let duper = match DuperParser::parse_duper_value(input) {
            Ok(duper) => duper,
            Err(error) => panic!("{:?}", miette::Error::new(error.into_miette())),
        };
        assert_eq!(
            duper,
            DuperValue {
                identifier: Some(DuperIdentifier(Cow::Borrowed("Product"))),
                inner: DuperInner::Object(DuperObject(vec![
                    (
                        DuperKey(Cow::Borrowed("product_id")),
                        DuperValue {
                            identifier: Some(DuperIdentifier(Cow::Borrowed("Uuid"))),
                            inner: DuperInner::String(DuperString(Cow::Borrowed(
                                "1dd7b7aa-515e-405f-85a9-8ac812242609"
                            ))),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("name")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::String(DuperString(Cow::Borrowed(
                                "Wireless Bluetooth Headphones"
                            ))),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("brand")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::String(DuperString(Cow::Borrowed("AudioTech"))),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("price")),
                        DuperValue {
                            identifier: Some(DuperIdentifier(Cow::Borrowed("Decimal"))),
                            inner: DuperInner::String(DuperString(Cow::Borrowed("129.99"))),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("dimensions")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::Tuple(DuperTuple(vec![
                                DuperValue {
                                    identifier: None,
                                    inner: DuperInner::Float(18.5)
                                },
                                DuperValue {
                                    identifier: None,
                                    inner: DuperInner::Float(15.2)
                                },
                                DuperValue {
                                    identifier: None,
                                    inner: DuperInner::Float(7.8)
                                },
                            ])),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("weight")),
                        DuperValue {
                            identifier: Some(DuperIdentifier(Cow::Borrowed("Weight"))),
                            inner: DuperInner::Float(0.285)
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("in_stock")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::Boolean(true),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("specifications")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::Object(DuperObject(vec![
                                (
                                    DuperKey(Cow::Borrowed("battery_life")),
                                    DuperValue {
                                        identifier: Some(DuperIdentifier(Cow::Borrowed(
                                            "Duration"
                                        ))),
                                        inner: DuperInner::String(DuperString(Cow::Borrowed(
                                            "30h"
                                        ))),
                                    }
                                ),
                                (
                                    DuperKey(Cow::Borrowed("noise_cancellation")),
                                    DuperValue {
                                        identifier: None,
                                        inner: DuperInner::Boolean(true),
                                    }
                                ),
                                (
                                    DuperKey(Cow::Borrowed("connectivity")),
                                    DuperValue {
                                        identifier: None,
                                        inner: DuperInner::Array(DuperArray(vec![
                                            DuperValue {
                                                identifier: None,
                                                inner: DuperInner::String(DuperString(
                                                    Cow::Borrowed("Bluetooth 5.0")
                                                ))
                                            },
                                            DuperValue {
                                                identifier: None,
                                                inner: DuperInner::String(DuperString(
                                                    Cow::Borrowed("3.5mm Jack")
                                                ))
                                            },
                                        ])),
                                    }
                                ),
                            ])),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("image_thumbnail")),
                        DuperValue {
                            identifier: Some(DuperIdentifier(Cow::Borrowed("Png"))),
                            inner: DuperInner::Bytes(DuperBytes(Cow::Borrowed(
                                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x64"
                            ))),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("tags")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::Array(DuperArray(vec![
                                DuperValue {
                                    identifier: None,
                                    inner: DuperInner::String(DuperString(Cow::Borrowed(
                                        "electronics"
                                    )))
                                },
                                DuperValue {
                                    identifier: None,
                                    inner: DuperInner::String(DuperString(Cow::Borrowed("audio")))
                                },
                                DuperValue {
                                    identifier: None,
                                    inner: DuperInner::String(DuperString(Cow::Borrowed(
                                        "wireless"
                                    )))
                                },
                            ])),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("release_date")),
                        DuperValue {
                            identifier: Some(DuperIdentifier(Cow::Borrowed("Date"))),
                            inner: DuperInner::String(DuperString(Cow::Borrowed("2023-11-15"))),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("warranty_period")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::Null,
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("customer_ratings")),
                        DuperValue {
                            identifier: None,
                            inner: DuperInner::Object(DuperObject(vec![
                                (
                                    DuperKey(Cow::Borrowed("latest_review")),
                                    DuperValue {
                                        identifier: None,
                                        inner: DuperInner::String(DuperString(Cow::Borrowed(
                                            r#"Absolutely ""astounding""!! 😎"#
                                        ))),
                                    }
                                ),
                                (
                                    DuperKey(Cow::Borrowed("average")),
                                    DuperValue {
                                        identifier: None,
                                        inner: DuperInner::Float(4.5)
                                    }
                                ),
                                (
                                    DuperKey(Cow::Borrowed("count")),
                                    DuperValue {
                                        identifier: None,
                                        inner: DuperInner::Integer(127)
                                    }
                                ),
                            ])),
                        }
                    ),
                    (
                        DuperKey(Cow::Borrowed("created_at")),
                        DuperValue {
                            identifier: Some(DuperIdentifier(Cow::Borrowed("DateTime"))),
                            inner: DuperInner::String(DuperString(Cow::Borrowed(
                                "2023-11-17T21:50:43+00:00"
                            ))),
                        }
                    ),
                ])),
            }
        );
    }
}
