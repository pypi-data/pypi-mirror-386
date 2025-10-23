use std::{borrow::Cow, collections::HashSet};

use pest::{
    error::{Error, ErrorVariant},
    iterators::Pair,
};

use crate::{
    ast::{
        DuperArray, DuperBytes, DuperIdentifier, DuperInner, DuperKey, DuperObject, DuperString,
        DuperTuple, DuperValue,
    },
    escape::{unescape_bytes, unescape_str},
    parser::Rule,
};

pub(crate) struct DuperBuilder;

impl DuperBuilder {
    pub(crate) fn build_duper(pair: Pair<'_, Rule>) -> Result<DuperValue<'_>, Box<Error<Rule>>> {
        Self::build_value(pair)
    }

    fn build_object(pair: Pair<'_, Rule>) -> Result<DuperObject<'_>, Box<Error<Rule>>> {
        debug_assert!(matches!(pair.as_rule(), Rule::object));
        let span = pair.as_span();
        let kv_pairs: Result<Vec<(DuperKey<'_>, DuperValue<'_>)>, _> = pair
            .into_inner()
            .map(|pair| {
                let span = pair.as_span();
                let mut inner_pair = pair.into_inner();
                let key_pair = inner_pair.next().unwrap();
                let key = match key_pair.as_rule() {
                    Rule::plain_key => Cow::Borrowed(key_pair.as_str()),
                    Rule::quoted_string => {
                        unescape_str(key_pair.into_inner().next().unwrap().as_str())
                            .expect("parsed valid escape sequences")
                    }
                    Rule::raw_string => {
                        Cow::Borrowed(key_pair.into_inner().next().unwrap().as_str())
                    }
                    rule => {
                        return Err(Box::new(Error::new_from_span(
                            ErrorVariant::CustomError {
                                message: format!("unexpected rule in object key {rule:?}"),
                            },
                            span,
                        )));
                    }
                };
                let value = Self::build_value(inner_pair.next().unwrap());
                value.map(|v| (DuperKey(key), v))
            })
            .collect();
        let kv_pairs = kv_pairs?;
        let unique_keys: HashSet<_> = kv_pairs.iter().map(|(k, _)| k).collect();
        if unique_keys.len() == kv_pairs.len() {
            Ok(DuperObject(kv_pairs))
        } else {
            Err(Box::new(Error::new_from_span(
                ErrorVariant::CustomError {
                    message: "duplicate keys in object".into(),
                },
                span,
            )))
        }
    }

    fn build_array(pair: Pair<'_, Rule>) -> Result<DuperArray<'_>, Box<Error<Rule>>> {
        debug_assert!(matches!(pair.as_rule(), Rule::array));
        let vec: Result<Vec<DuperValue<'_>>, _> = pair
            .into_inner()
            .map(|pair| Self::build_value(pair))
            .collect();
        Ok(DuperArray(vec?))
    }

    fn build_tuple(pair: Pair<'_, Rule>) -> Result<DuperTuple<'_>, Box<Error<Rule>>> {
        debug_assert!(matches!(pair.as_rule(), Rule::tuple));
        let vec: Result<Vec<DuperValue<'_>>, _> = pair
            .into_inner()
            .map(|pair| Self::build_value(pair))
            .collect();
        Ok(DuperTuple(vec?))
    }

    fn build_value(pair: Pair<'_, Rule>) -> Result<DuperValue<'_>, Box<Error<Rule>>> {
        let span = pair.as_span();
        let mut inner_pair = pair.into_inner();
        let mut next = inner_pair.next().unwrap();
        let identifier = match next.as_rule() {
            Rule::identifier => {
                let identifier = next.as_str();
                next = inner_pair.next().unwrap();
                Some(DuperIdentifier(Cow::Borrowed(identifier)))
            }
            _ => None,
        };
        Ok(DuperValue {
            identifier,
            inner: match next.as_rule() {
                Rule::object => DuperInner::Object(Self::build_object(next)?),
                Rule::array => DuperInner::Array(Self::build_array(next)?),
                Rule::tuple => DuperInner::Tuple(Self::build_tuple(next)?),
                Rule::quoted_string => DuperInner::String(DuperString(
                    unescape_str(next.into_inner().next().unwrap().as_str())
                        .expect("parsed valid escape sequences"),
                )),
                Rule::raw_string => DuperInner::String(DuperString(Cow::Borrowed(
                    next.into_inner().next().unwrap().as_str(),
                ))),
                Rule::quoted_bytes => DuperInner::Bytes(DuperBytes(
                    unescape_bytes(next.into_inner().next().unwrap().as_str())
                        .expect("parsed valid escape sequences"),
                )),
                Rule::raw_bytes => DuperInner::Bytes(DuperBytes(Cow::Borrowed(
                    next.into_inner().next().unwrap().as_str().as_bytes(),
                ))),
                Rule::integer => DuperInner::Integer({
                    let integer_inner = next.into_inner().next().unwrap();
                    match integer_inner.as_rule() {
                        Rule::decimal_integer => integer_inner.as_str().parse().unwrap(),
                        Rule::hex_integer => {
                            i64::from_str_radix(integer_inner.as_str().split_at(2).1, 16).unwrap()
                        }
                        Rule::octal_integer => {
                            i64::from_str_radix(integer_inner.as_str().split_at(2).1, 8).unwrap()
                        }
                        Rule::binary_integer => {
                            i64::from_str_radix(integer_inner.as_str().split_at(2).1, 2).unwrap()
                        }
                        rule => {
                            return Err(Box::new(Error::new_from_span(
                                ErrorVariant::CustomError {
                                    message: format!("unexpected rule in integer value {rule:?}"),
                                },
                                span,
                            )));
                        }
                    }
                }),
                Rule::float => DuperInner::Float(next.as_str().replace('_', "").parse().unwrap()),
                Rule::boolean => DuperInner::Boolean(next.as_str().parse().unwrap()),
                Rule::null => DuperInner::Null,
                rule => {
                    return Err(Box::new(Error::new_from_span(
                        ErrorVariant::CustomError {
                            message: format!("unexpected rule in value {rule:?}"),
                        },
                        span,
                    )));
                }
            },
        })
    }
}
